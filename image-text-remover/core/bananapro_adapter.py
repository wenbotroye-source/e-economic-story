"""
NanoBanana PRO 图片编辑适配器
通过 own-jarvis-api.com 调用 Gemini 原生格式 API（snake_case）
"""

import io
import base64
from typing import Optional, Callable
from dataclasses import dataclass

import requests
from PIL import Image

from .image_utils import load_image, image_to_base64


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    image: Optional[Image.Image] = None
    message: str = ""


class NanoBananaProAdapter:
    """NanoBanana PRO 图片编辑适配器"""

    def __init__(self, api_key: str = "sk-gNcpfR60ul6itd6TU7OnP2TIxBlOYXvRa77WIsKSCFTT6in6",
                 model: str = "gemini-2.5-flash-image"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://own-jarvis-api.com"

    def process_image(self,
                     image_path: str,
                     prompt: str,
                     reference_images: Optional[list] = None,
                     progress_callback: Optional[Callable[[str, int], None]] = None) -> ProcessingResult:
        """处理单张图片"""
        try:
            # 1. 加载 + 转 base64
            if progress_callback:
                progress_callback("加载图片...", 10)

            encoded = load_and_encode(image_path)
            if not encoded:
                return ProcessingResult(success=False, message="加载输入图片失败，请检查路径或网络")
            image_base64, mime_type = encoded

            # 2. 加载参考图
            ref_data_list = []
            if reference_images:
                if progress_callback:
                    progress_callback(f"加载 {len(reference_images)} 张参考图...", 25)
                for ref_path in reference_images:
                    ref_encoded = load_and_encode(ref_path)
                    if ref_encoded:
                        ref_data_list.append(ref_encoded)

            # 3. 调用 API
            if progress_callback:
                progress_callback("调用 NanoBanana PRO API...", 30)

            result_image = self._call_api(image_base64, mime_type, prompt, ref_data_list)

            if not result_image:
                return ProcessingResult(success=False, message="NanoBanana PRO API 处理失败")

            if progress_callback:
                progress_callback("完成!", 100)

            return ProcessingResult(success=True, image=result_image, message="处理成功")

        except Exception as e:
            return ProcessingResult(success=False, message=f"处理失败: {str(e)}")

    def _call_api(self, image_base64: str, mime_type: str, prompt: str,
                  ref_data_list: list = None) -> Optional[Image.Image]:
        """调用 NanoBanana PRO API"""
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        parts = []
        if ref_data_list:
            for ref_b64, ref_mime in ref_data_list:
                parts.append({"inline_data": {"mime_type": ref_mime, "data": ref_b64}})
        parts.append({"inline_data": {"mime_type": mime_type, "data": image_base64}})
        parts.append({"text": prompt})

        request_data = {
            "contents": [{"role": "user", "parts": parts}],
            "generation_config": {"response_modalities": ["IMAGE"]}
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        print(f"[API] 请求: {url[:80]}...")
        print(f"[API] parts: {len(parts)}, 请求体: {len(str(request_data))} 字符")

        try:
            response = requests.post(url, headers=headers, json=request_data, timeout=300)
            data = response.json()

            if not response.ok:
                error_msg = data.get('error', {}).get('message', response.text[:500])
                raise Exception(f"API 错误 ({response.status_code}): {error_msg}")

            candidates = data.get('candidates', [])
            if not candidates:
                raise Exception("API 返回空结果")

            content = candidates[0].get('content', {})
            resp_parts = content.get('parts', [])

            for i, part in enumerate(resp_parts):
                # 支持 snake_case 和 camelCase
                inline_data = part.get('inline_data') or part.get('inlineData')
                if inline_data and 'data' in inline_data:
                    b64 = inline_data['data']
                    print(f"[API] 收到图片, base64长度: {len(b64)}")
                    return base64_to_image(b64)

                file_data = part.get('file_data') or part.get('fileData')
                if file_data:
                    file_url = file_data.get('fileUri') or file_data.get('file_uri', '')
                    if file_url:
                        print(f"[API] 从URL下载: {file_url[:80]}...")
                        img_resp = requests.get(file_url, timeout=120)
                        img_resp.raise_for_status()
                        return Image.open(io.BytesIO(img_resp.content))

                if 'text' in part:
                    print(f"[API] 文本响应: {part['text'][:100]}")

            text_parts = [p.get('text', '') for p in resp_parts if 'text' in p]
            if text_parts:
                raise Exception(f"API 返回文本而非图片: {' '.join(text_parts)}")

            raise Exception(f"API 响应中未找到图片")

        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")


# 从 image_utils 导入 base64_to_image（_call_api 用到）
from .image_utils import load_and_encode, base64_to_image

# 兼容性别名
BananaProAdapter = NanoBananaProAdapter


def process_with_nanobanana_pro(image_path: str,
                                 api_key: str = "sk-gNcpfR60ul6itd6TU7OnP2TIxBlOYXvRa77WIsKSCFTT6in6",
                                 prompt: Optional[str] = None,
                                 model: str = "gemini-2.5-flash-image") -> ProcessingResult:
    """便捷函数：使用 NanoBanana PRO 处理图片"""
    if not prompt:
        prompt = "Enhance this product photo by cleaning up the background."
    adapter = NanoBananaProAdapter(api_key, model)
    return adapter.process_image(image_path, prompt)


# 兼容旧接口
def process_with_bananapro(image_path: str, api_key: str,
                            prompt: Optional[str] = None,
                            model: str = "gemini-2.5-flash-image") -> ProcessingResult:
    """兼容旧接口"""
    return process_with_nanobanana_pro(image_path, api_key, prompt, model)
