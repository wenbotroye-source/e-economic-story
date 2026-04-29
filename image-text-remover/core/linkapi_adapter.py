"""
LinkAPI.ai 图像处理适配器
支持通过 LinkAPI.ai 进行图像生成/编辑
"""

import io
import base64
from typing import Optional, Callable
from dataclasses import dataclass

import requests
from PIL import Image

from .image_utils import load_image, image_to_base64, load_and_encode


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    image: Optional[Image.Image] = None
    message: str = ""


class LinkAPIAdapter:
    """LinkAPI.ai 图像处理适配器"""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-image"):
        """
        初始化适配器

        Args:
            api_key: LinkAPI.ai API Key
            model: 模型名称，默认使用 gemini-2.5-flash-image
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://linkapi.ai"
        self.endpoint = f"/v1beta/models/{model}:generateContent"

    def process_image(self,
                     image_path: str,
                     prompt: str,
                     reference_images: Optional[list] = None,
                     progress_callback: Optional[Callable[[str, int], None]] = None) -> ProcessingResult:
        """
        处理单张图片

        Args:
            image_path: 图片路径（本地路径）
            prompt: 编辑提示词
            reference_images: 可选的参考图路径列表
            progress_callback: 进度回调函数

        Returns:
            ProcessingResult: 处理结果
        """
        try:
            # 1. 加载 + 转 base64
            if progress_callback:
                progress_callback("加载图片...", 10)

            encoded = load_and_encode(image_path)
            if not encoded:
                return ProcessingResult(success=False, message="加载输入图片失败，请检查路径")
            image_base64, mime_type = encoded

            # 保留原始图片用于 NO_IMAGE 回退
            input_image = load_image(image_path)

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
                progress_callback("调用 API...", 30)

            result_image = self._call_linkapi_api(image_base64, mime_type, prompt, input_image, ref_data_list)

            if not result_image:
                return ProcessingResult(success=False, message="LinkAPI.ai API 处理失败")

            if progress_callback:
                progress_callback("完成!", 100)

            return ProcessingResult(
                success=True,
                image=result_image,
                message="处理成功"
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                message=f"处理失败: {str(e)}"
            )

    def _call_linkapi_api(self, image_base64: str, mime_type: str, prompt: str, input_image: Image.Image, ref_data_list: list = None) -> Optional[Image.Image]:
        """
        调用 LinkAPI.ai API 进行图像编辑

        Args:
            image_base64: base64 编码的主图
            mime_type: 主图 MIME 类型
            prompt: 编辑提示词
            input_image: 原始输入图片（用于NO_IMAGE情况）
            ref_data_list: 参考图列表 [(base64, mime_type), ...]

        Returns:
            PIL Image 或 None
        """
        url = f"{self.base_url}{self.endpoint}"

        # 构建 parts：参考图在前，主图在后，最后是提示词
        parts = []

        if ref_data_list:
            for ref_b64, ref_mime in ref_data_list:
                parts.append({
                    "inline_data": {
                        "mime_type": ref_mime,
                        "data": ref_b64
                    }
                })

        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": image_base64
            }
        })

        parts.append({
            "text": prompt
        })

        # 构造请求体
        request_data = {
            "contents": [{
                "role": "user",
                "parts": parts
            }],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            # 增加超时时间到 300 秒（5分钟）
            response = requests.post(url, headers=headers, json=request_data, timeout=300)

            # 解析响应
            try:
                data = response.json()
            except:
                raise Exception(f"解析响应失败: {response.text[:200]}")

            if not response.ok:
                error_msg = data.get('error', {}).get('message', response.text[:500])
                raise Exception(f"API 错误 ({response.status_code}): {error_msg}")

            # 提取生成的图片
            candidates = data.get('candidates', [])
            if not candidates:
                raise Exception("API 返回空结果")

            # 检查完成原因
            finish_reason = candidates[0].get('finishReason')
            finish_message = candidates[0].get('finishMessage', '')

            if finish_reason == 'NO_IMAGE':
                print(f"[调试] API 返回 NO_IMAGE，操作未被执行")
                raise Exception("API 未能处理图片（返回 NO_IMAGE）。可能原因：提示词不受支持，或图片无需修改")
            elif finish_reason == 'MALFORMED_FUNCTION_CALL':
                print(f"[调试] API 返回 MALFORMED_FUNCTION_CALL: {finish_message}")
                print(f"[调试] 完整响应: {data}")
                raise Exception(f"API 请求格式错误: {finish_message}")

            content = candidates[0].get('content', {})
            parts = content.get('parts', [])

            # 查找图片部分 (API 返回驼峰命名 inlineData)
            for part in parts:
                # 尝试两种命名方式
                inline_data = part.get('inlineData') or part.get('inline_data')
                if inline_data:
                    image_data = base64.b64decode(inline_data['data'])
                    return Image.open(io.BytesIO(image_data))

            # 如果没有图片，检查是否有错误信息
            text_parts = [part.get('text', '') for part in parts if 'text' in part]
            if text_parts:
                raise Exception(f"API 返回文本而非图片: {' '.join(text_parts)}")

            # 打印完整响应用于调试
            print(f"[调试] API 完整响应: {data}")
            raise Exception(f"API 响应中未找到图片。parts 数量: {len(parts)}, 内容: {parts}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")


def process_with_linkapi(image_path: str,
                        api_key: str,
                        prompt: Optional[str] = None,
                        model: str = "gemini-2.5-flash-image") -> ProcessingResult:
    """
    便捷函数：使用 LinkAPI.ai 处理图片

    Args:
        image_path: 图片路径（本地路径）
        api_key: LinkAPI.ai API Key
        prompt: 可选的自定义提示词
        model: 模型名称

    Returns:
        ProcessingResult: 处理结果
    """
    if not prompt:
        prompt = "Clean up the image by removing text overlays and signatures. Keep the product intact."

    adapter = LinkAPIAdapter(api_key, model)
    return adapter.process_image(image_path, prompt)