"""
OCR 客户端 - 支持多服务商
预留接口：可轻松添加新的OCR服务商
"""

import os
import base64
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import io


class BaseOCRClient(ABC):
    """OCR客户端基类 - 所有服务商需继承此类"""

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.name = "base"

    @abstractmethod
    def detect_text(self, image_path: str) -> List[Dict[str, Any]]:
        """
        检测图片中的文字

        Args:
            image_path: 图片路径

        Returns:
            识别结果列表，每项包含:
            - text: 识别到的文字
            - box: 边界框坐标 [x1, y1, x2, y2]
            - confidence: 置信度 (可选)
        """
        pass

    def _image_to_base64(self, image_path: str) -> str:
        """将图片转为base64字符串"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _resize_if_needed(self, image_path: str, max_size: int = 4096) -> Image.Image:
        """如果图片过大，进行压缩"""
        img = Image.open(image_path)
        width, height = img.size

        if width > max_size or height > max_size:
            ratio = min(max_size / width, max_size / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        return img


class NanoBananaOCRClient(BaseOCRClient):
    """Nano Banana OCR 客户端"""

    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.name = "nano_banana"
        self.api_key = config.get('NANO_BANANA_API_KEY', '')
        self.endpoint = config.get('NANO_BANANA_OCR_ENDPOINT', '')

    def detect_text(self, image_path: str) -> List[Dict[str, Any]]:
        """调用 Nano Banana OCR API"""
        if not self.api_key or not self.endpoint:
            raise ValueError("请配置 NANO_BANANA_API_KEY 和 NANO_BANANA_OCR_ENDPOINT")

        # 压缩图片（如果需要）
        img = self._resize_if_needed(image_path)

        # 转为base64
        buffer = io.BytesIO()
        img_format = 'JPEG' if img.mode in ('RGB', 'L') else 'PNG'
        img.save(buffer, format=img_format)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # 构建请求
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # TODO: 根据实际Nano Banana API文档调整请求格式
        payload = {
            'image': f'data:image/{img_format.lower()};base64,{img_base64}',
            # 可能需要其他参数，请参考 Nano Banana 文档
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Nano Banana OCR API 调用失败: {e}")

    def _parse_response(self, data: Dict) -> List[Dict[str, Any]]:
        """解析 Nano Banana 返回结果"""
        # TODO: 根据实际API返回格式调整解析逻辑
        # 以下是一个示例格式
        results = []

        # 假设返回格式: { "predictions": [{"text": "...", "box": [x1,y1,x2,y2], "confidence": 0.95}] }
        predictions = data.get('predictions', []) or data.get('result', []) or data.get('data', [])

        for item in predictions:
            results.append({
                'text': item.get('text', ''),
                'box': item.get('box', item.get('bbox', [0, 0, 0, 0])),
                'confidence': item.get('confidence', 0.0)
            })

        return results


class PaddleOCRClient(BaseOCRClient):
    """PaddleOCR 客户端 - 预留接口"""

    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.name = "paddleocr"
        self.api_key = config.get('PADDLEOCR_API_KEY', '')
        self.endpoint = config.get('PADDLEOCR_ENDPOINT', '')

    def detect_text(self, image_path: str) -> List[Dict[str, Any]]:
        """调用 PaddleOCR API 或本地模型"""
        # TODO: 实现 PaddleOCR 调用逻辑
        # 如果使用本地模型，可以导入 paddleocr 库
        # from paddleocr import PaddleOCR
        # ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        # result = ocr.ocr(image_path, cls=True)
        raise NotImplementedError("PaddleOCR 客户端待实现 - 请根据实际部署方式实现")


class EasyOCRClient(BaseOCRClient):
    """EasyOCR 客户端 - 预留接口"""

    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.name = "easyocr"
        self.api_key = config.get('EASYOCR_API_KEY', '')
        self.endpoint = config.get('EASYOCR_ENDPOINT', '')

    def detect_text(self, image_path: str) -> List[Dict[str, Any]]:
        """调用 EasyOCR API 或本地模型"""
        # TODO: 实现 EasyOCR 调用逻辑
        # import easyocr
        # reader = easyocr.Reader(['ch_sim', 'en'])
        # result = reader.readtext(image_path)
        raise NotImplementedError("EasyOCR 客户端待实现 - 请根据实际部署方式实现")


class BaiduOCRClient(BaseOCRClient):
    """百度智能云 OCR 客户端 - 预留接口"""

    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.name = "baidu"
        self.app_id = config.get('BAIDU_APP_ID', '')
        self.api_key = config.get('BAIDU_API_KEY', '')
        self.secret_key = config.get('BAIDU_SECRET_KEY', '')
        self.access_token = None

    def _get_access_token(self) -> str:
        """获取百度API访问令牌"""
        # TODO: 实现百度API Token获取
        # https://ai.baidu.com/ai-doc/OCR/1k3h7y3db
        raise NotImplementedError("百度OCR客户端待实现")

    def detect_text(self, image_path: str) -> List[Dict[str, Any]]:
        """调用百度OCR API"""
        # TODO: 实现百度OCR调用
        raise NotImplementedError("百度OCR客户端待实现 - 请参考百度智能云文档实现")


class AliyunOCRClient(BaseOCRClient):
    """阿里云视觉智能 OCR 客户端 - 预留接口"""

    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.name = "aliyun"
        self.access_key_id = config.get('ALIYUN_ACCESS_KEY_ID', '')
        self.access_key_secret = config.get('ALIYUN_ACCESS_KEY_SECRET', '')
        self.endpoint = config.get('ALIYUN_ENDPOINT', 'ocr.aliyuncs.com')

    def detect_text(self, image_path: str) -> List[Dict[str, Any]]:
        """调用阿里云OCR API"""
        # TODO: 实现阿里云OCR调用
        raise NotImplementedError("阿里云OCR客户端待实现 - 请参考阿里云视觉智能文档实现")


# ============================================
# 工厂函数：创建对应的OCR客户端
# ============================================

def create_ocr_client(provider: str = None) -> BaseOCRClient:
    """
    创建OCR客户端

    Args:
        provider: 服务商名称，默认从环境变量读取 OCR_PROVIDER

    Returns:
        OCR客户端实例
    """
    from dotenv import load_dotenv
    load_dotenv()

    if provider is None:
        provider = os.getenv('OCR_PROVIDER', 'nano_banana')

    # 收集所有相关配置
    config = dict(os.environ)

    # 根据服务商创建对应客户端
    if provider == 'nano_banana':
        return NanoBananaOCRClient(config)
    elif provider == 'paddleocr':
        return PaddleOCRClient(config)
    elif provider == 'easyocr':
        return EasyOCRClient(config)
    elif provider == 'baidu':
        return BaiduOCRClient(config)
    elif provider == 'aliyun':
        return AliyunOCRClient(config)
    else:
        raise ValueError(f"不支持的OCR服务商: {provider}")


# ============================================
# 使用示例
# ============================================

if __name__ == '__main__':
    # 测试OCR客户端
    try:
        client = create_ocr_client()
        print(f"使用OCR服务商: {client.name}")

        # 测试图片路径
        test_image = "input/test.jpg"

        if os.path.exists(test_image):
            results = client.detect_text(test_image)
            print(f"识别到 {len(results)} 个文本区域:")
            for r in results:
                print(f"  - '{r['text']}' @ {r['box']}")
        else:
            print(f"测试图片不存在: {test_image}")

    except Exception as e:
        print(f"错误: {e}")
