"""
OpenAI GPT Image API 适配器
支持通过 OpenAI images/edits 接口进行图像编辑（gpt-image-2）
"""

import io
import base64
from typing import Optional, Callable
from dataclasses import dataclass

import requests
from PIL import Image

from .image_utils import load_image


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    image: Optional[Image.Image] = None
    message: str = ""


class OpenAIImageAdapter:
    """OpenAI GPT Image API 适配器"""

    def __init__(self, api_key: str, model: str = "gpt-image-2", base_url: str = None):
        self.api_key = api_key
        self.model = model
        if base_url:
            # 自定义中转站地址，自动拼接 /v1/images/edits 路径
            self.base_url = base_url.rstrip("/") + "/v1/images/edits"
        else:
            self.base_url = "https://api.openai.com/v1/images/edits"

    def process_image(self,
                     image_path: str,
                     prompt: str,
                     reference_images: Optional[list] = None,
                     progress_callback: Optional[Callable[[str, int], None]] = None) -> "ProcessingResult":
        try:
            if progress_callback:
                progress_callback("加载图片...", 10)

            img = load_image(image_path)
            if not img:
                return ProcessingResult(success=False, message="加载输入图片失败，请检查路径或网络")

            # 转为 JPEG 字节流（匹配接口格式）
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG", quality=95)
            img_bytes.seek(0)

            # 加载参考图
            ref_bytes_list = []
            if reference_images:
                if progress_callback:
                    progress_callback(f"加载 {len(reference_images)} 张参考图...", 20)
                for ref_path in reference_images:
                    ref_img = load_image(ref_path)
                    if ref_img:
                        if ref_img.mode in ("RGBA", "LA", "P"):
                            ref_img = ref_img.convert("RGB")
                        ref_buf = io.BytesIO()
                        ref_img.save(ref_buf, format="JPEG", quality=95)
                        ref_buf.seek(0)
                        ref_bytes_list.append(ref_buf)

            if progress_callback:
                progress_callback("调用 OpenAI GPT Image API...", 30)

            result_image = self._call_edit_api(img_bytes, prompt, ref_bytes_list)

            if not result_image:
                return ProcessingResult(success=False, message="OpenAI API 处理失败")

            if progress_callback:
                progress_callback("完成!", 100)

            return ProcessingResult(success=True, image=result_image, message="处理成功")

        except Exception as e:
            return ProcessingResult(success=False, message=f"处理失败: {str(e)}")

    def _call_edit_api(self, image_bytes: io.BytesIO, prompt: str,
                       ref_bytes_list: Optional[list] = None) -> Optional[Image.Image]:
        """
        调用 OpenAI images/edits 接口

        Args:
            image_bytes: 主图 JPEG 字节流
            prompt: 编辑提示词
            ref_bytes_list: 参考图 JPEG 字节流列表

        Returns:
            PIL Image 或 None
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        # 构建多图片文件列表（与 image_edit.py 格式一致）
        files = []
        # 参考图在前
        if ref_bytes_list:
            for i, ref_buf in enumerate(ref_bytes_list):
                files.append(('image', (f'ref_{i}.jpg', ref_buf, 'image/jpeg')))
        # 主图在后
        files.append(('image', ('image.jpg', image_bytes, 'image/jpeg')))

        data = {
            "model": self.model,
            "prompt": prompt,
            "n": "1",
            "size": "1024x1536",
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                files=files,
                data=data,
                timeout=600,
            )

            try:
                resp_json = response.json()
            except Exception:
                raise Exception(f"解析响应失败: {response.text[:200]}")

            if not response.ok:
                error_msg = resp_json.get("error", {}).get("message", response.text[:500])
                raise Exception(f"API 错误 ({response.status_code}): {error_msg}")

            # 解析返回的图片数据
            result_data = resp_json.get("data", [])
            if not result_data:
                raise Exception("API 返回空结果")

            item = result_data[0]

            # 优先取 base64（b64_json 字段）
            b64 = item.get("b64_json")
            if b64:
                image_data = base64.b64decode(b64)
                return Image.open(io.BytesIO(image_data))

            # 回退取 URL
            url = item.get("url")
            if url:
                img_resp = requests.get(url, timeout=120)
                img_resp.raise_for_status()
                return Image.open(io.BytesIO(img_resp.content))

            raise Exception(f"API 响应中未找到图片数据: {item}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")


def process_with_openai(image_path: str,
                        api_key: str,
                        prompt: str = None,
                        model: str = "gpt-image-2") -> ProcessingResult:
    """便捷函数：使用 OpenAI GPT Image 处理图片"""
    if not prompt:
        prompt = "Remove all text, watermarks, and logos from this image while keeping the product intact."

    adapter = OpenAIImageAdapter(api_key, model)
    return adapter.process_image(image_path, prompt)
