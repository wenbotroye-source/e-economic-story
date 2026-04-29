"""
统一API适配器 - 支持多服务商
通过配置自动适配不同API格式
"""

import base64
import io
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

import requests
from PIL import Image

from .config import ConfigManager, get_config


@dataclass
class TextDetection:
    """文字检测结果"""
    text: str
    box: List[int]  # [x1, y1, x2, y2]
    confidence: float = 0.0


@dataclass
class InpaintResult:
    """图像修复结果"""
    image: Image.Image
    metadata: Dict[str, Any]


class BaseAPIAdapter(ABC):
    """API适配器基类"""

    def __init__(self, provider_config: Dict[str, Any]):
        self.config = provider_config
        self.name = provider_config.get('name', 'unknown')
        self.base_url = provider_config.get('base_url', '')
        self.auth_config = provider_config.get('auth', {})
        self.request_config = provider_config.get('request_format', {})
        self.response_config = provider_config.get('response_mapping', {})

    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        auth_type = self.auth_config.get('type', 'none')
        headers = {'Content-Type': 'application/json'}

        if auth_type == 'bearer':
            api_key = self.auth_config.get('api_key', '')
            headers['Authorization'] = f'Bearer {api_key}'
        elif auth_type == 'header':
            header_name = self.auth_config.get('header_name', 'X-API-Key')
            api_key = self.auth_config.get('api_key', '')
            headers[header_name] = api_key

        return headers

    def _encode_image(self, image: Image.Image) -> str:
        """编码图片"""
        encoding = self.request_config.get('image_encoding', 'base64')

        if encoding == 'base64':
            buffer = io.BytesIO()
            fmt = 'JPEG' if image.mode in ('RGB', 'L') else 'PNG'
            image.save(buffer, format=fmt)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

        elif encoding == 'base64_datauri':
            buffer = io.BytesIO()
            fmt = 'JPEG' if image.mode in ('RGB', 'L') else 'PNG'
            ext = fmt.lower()
            image.save(buffer, format=fmt)
            b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f'data:image/{ext};base64,{b64}'

        elif encoding == 'url':
            # TODO: 上传图片到临时存储并返回URL
            raise NotImplementedError("URL编码需要实现图片上传功能")

        else:
            raise ValueError(f"不支持的编码格式: {encoding}")

    def _resize_if_needed(self, image: Image.Image, max_size: int = 4096) -> Image.Image:
        """调整图片大小"""
        width, height = image.size
        if width > max_size or height > max_size:
            ratio = min(max_size / width, max_size / height)
            new_size = (int(width * ratio), int(height * ratio))
            return image.resize(new_size, Image.LANCZOS)
        return image

    def _extract_from_path(self, data: Any, path: str):
        """从嵌套字典中提取值"""
        if not path:
            return data

        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                current = current[int(key)] if int(key) < len(current) else None
            else:
                return None
            if current is None:
                return None
        return current


class OCRAdapter(BaseAPIAdapter):
    """OCR API适配器"""

    def detect(self, image_path: str) -> List[TextDetection]:
        """检测图片中的文字"""
        # 加载并预处理图片
        image = Image.open(image_path)
        image = self._resize_if_needed(image)

        # 构建请求
        image_field = self.request_config.get('image_field', 'image')
        payload = {image_field: self._encode_image(image)}

        # 添加额外参数
        extra_params = self.request_config.get('extra_params', {})
        payload.update(extra_params)

        # 发送请求
        endpoint = self.request_config.get('endpoint', '/predict')
        url = f"{self.base_url}{endpoint}"

        method = self.request_config.get('method', 'POST')
        headers = self._get_auth_headers()

        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, json=payload, timeout=60)
            else:
                response = requests.get(url, headers=headers, params=payload, timeout=60)

            response.raise_for_status()
            return self._parse_response(response.json())

        except requests.exceptions.RequestException as e:
            raise Exception(f"OCR API调用失败 ({self.name}): {e}")

    def _parse_response(self, data: Dict) -> List[TextDetection]:
        """解析API响应"""
        results_path = self.response_config.get('results_path', '')
        items = self._extract_from_path(data, results_path) or data

        if not isinstance(items, list):
            items = [items]

        text_field = self.response_config.get('text_field', 'text')
        box_field = self.response_config.get('box_field', 'box')
        conf_field = self.response_config.get('confidence_field', 'confidence')

        detections = []
        for item in items:
            if isinstance(item, dict):
                text = self._extract_from_path(item, text_field) or ''
                box = self._extract_from_path(item, box_field) or [0, 0, 0, 0]
                conf = self._extract_from_path(item, conf_field) or 0.0

                # 标准化box格式为 [x1, y1, x2, y2]
                if isinstance(box, dict):
                    # 百度格式: {left, top, width, height}
                    x1 = box.get('left', box.get('x', 0))
                    y1 = box.get('top', box.get('y', 0))
                    w = box.get('width', 0)
                    h = box.get('height', 0)
                    box = [x1, y1, x1 + w, y1 + h]

                detections.append(TextDetection(
                    text=str(text),
                    box=box if isinstance(box, list) else [0, 0, 0, 0],
                    confidence=float(conf) if conf else 0.0
                ))

        return detections


class InpaintAdapter(BaseAPIAdapter):
    """通用图像修复API适配器"""

    def inpaint(self, image: Image.Image, mask: Image.Image,
                prompt_config: Optional[Any] = None) -> Image.Image:
        """修复图片"""
        # 预处理
        image = self._resize_if_needed(image)
        mask = mask.resize(image.size, Image.NEAREST)

        # 构建请求
        image_field = self.request_config.get('image_field', 'image')
        mask_field = self.request_config.get('mask_field', 'mask')

        payload = {
            image_field: self._encode_image(image),
            mask_field: self._encode_image(mask)
        }

        # 添加prompt（如果需要）
        if prompt_config and self.request_config.get('prompt_field'):
            prompt_field = self.request_config['prompt_field']
            payload[prompt_field] = prompt_config.positive

            # 某些API支持negative prompt
            neg_field = self.request_config.get('negative_prompt_field')
            if neg_field:
                payload[neg_field] = prompt_config.negative

        # 添加额外参数
        extra_params = self.request_config.get('extra_params', {})
        payload.update(extra_params)

        # 发送请求
        endpoint = self.request_config.get('endpoint', '/predict')
        url = f"{self.base_url}{endpoint}"

        method = self.request_config.get('method', 'POST')
        headers = self._get_auth_headers()

        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, json=payload, timeout=120)
            else:
                response = requests.get(url, headers=headers, params=payload, timeout=120)

            response.raise_for_status()
            return self._parse_response(response.json())

        except requests.exceptions.RequestException as e:
            raise Exception(f"Inpaint API调用失败 ({self.name}): {e}")

    def _parse_response(self, data: Dict) -> Image.Image:
        """解析API响应"""
        result_field = self.response_config.get('result_field', 'output')
        result = self._extract_from_path(data, result_field) or data

        # 如果结果是base64字符串
        if isinstance(result, str):
            # 移除data URI前缀
            if ',' in result:
                result = result.split(',')[1]
            img_data = base64.b64decode(result)
            return Image.open(io.BytesIO(img_data))

        # 如果结果是URL
        elif isinstance(result, str) and result.startswith('http'):
            response = requests.get(result, timeout=60)
            return Image.open(io.BytesIO(response.content))

        else:
            raise ValueError(f"无法解析修复结果: {type(result)}")


def create_ocr_adapter(provider_name: Optional[str] = None) -> OCRAdapter:
    """创建OCR适配器"""
    config = get_config()
    if provider_name is None:
        provider_name = config.get_default_provider('ocr')

    # 服务商名称映射
    provider_mapping = {
        'nano_banana': 'nano_banana_ocr',
        'qianwen': 'qianwen_ocr',
        'seedream': 'seedream_ocr',
        'wan': 'wan_ocr',
        'baidu': 'baidu_ocr',
        'aliyun': 'aliyun_ocr',
    }

    actual_name = provider_mapping.get(provider_name, provider_name)
    provider_config = config.get_provider_config(actual_name)
    return OCRAdapter(provider_config)


class LinkAPIAdapter(BaseAPIAdapter):
    """LinkAPI.ai 图像修复API适配器"""

    def inpaint(self, image: Image.Image, mask: Image.Image,
                prompt_config: Optional[Any] = None) -> Image.Image:
        """修复图片"""
        # 预处理
        image = self._resize_if_needed(image)
        mask = mask.resize(image.size, Image.NEAREST)

        # 构建请求 - 使用LinkAPI.ai特定格式
        image_base64, mime_type = self._encode_image_with_mime(image)

        # 获取提示词
        prompt = ""
        if prompt_config and hasattr(prompt_config, 'positive'):
            prompt = prompt_config.positive

        # 构造LinkAPI.ai请求体
        request_data = {
            "contents": [{
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_base64
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }

        # 发送请求
        endpoint = self.request_config.get('endpoint', '/v1beta/models/gemini-3-pro-image-preview:generateContent')
        url = f"{self.base_url}{endpoint}"

        headers = self._get_auth_headers()
        # LinkAPI.ai使用特殊的认证头
        headers['x-goog-api-key'] = self.auth_config.get('api_key', '')

        try:
            response = requests.post(url, headers=headers, json=request_data, timeout=300)
            response.raise_for_status()
            return self._parse_response(response.json())

        except requests.exceptions.RequestException as e:
            raise Exception(f"LinkAPI.ai API调用失败 ({self.name}): {e}")

    def _encode_image_with_mime(self, image: Image.Image) -> tuple:
        """编码图片并返回base64和mime_type"""
        # 转换为 RGB 模式（去除 alpha 通道）
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')

        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)

        image_bytes = buffer.getvalue()
        base64_string = base64.b64encode(image_bytes).decode('utf-8')

        return base64_string, "image/jpeg"

    def _parse_response(self, data: Dict) -> Image.Image:
        """解析API响应"""
        # 提取生成的图片
        candidates = data.get('candidates', [])
        if not candidates:
            raise Exception("API 返回空结果")

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

        raise Exception(f"API 响应中未找到图片。parts 数量: {len(parts)}")


def create_inpaint_adapter(provider_name: Optional[str] = None) -> InpaintAdapter:
    """创建Inpaint适配器"""
    config = get_config()
    if provider_name is None:
        provider_name = config.get_default_provider('inpaint')

    # 服务商名称映射
    provider_mapping = {
        'nano_banana': 'nano_banana_inpaint',
        'qianwen': 'qianwen_inpaint',
        'seedream': 'seedream_inpaint',
        'wan': 'wan_inpaint',
        'sd': 'sd_inpaint',
        'replicate': 'replicate_inpaint',
        'linkapi': 'linkapi_inpaint',
        'linkapi_ai': 'linkapi_inpaint',
    }

    actual_name = provider_mapping.get(provider_name, provider_name)
    provider_config = config.get_provider_config(actual_name)

    # 特殊处理LinkAPI.ai适配器
    if 'linkapi' in actual_name:
        return LinkAPIAdapter(provider_config)

    return InpaintAdapter(provider_config)
