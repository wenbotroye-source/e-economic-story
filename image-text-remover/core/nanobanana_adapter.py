"""
NanoBanana 图片编辑适配器
简化版：直接使用用户提供的图片 URL 进行编辑
"""

import io
import time
from typing import Optional
from dataclasses import dataclass

import requests
from PIL import Image


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    image: Optional[Image.Image] = None
    message: str = ""


class NanoBananaAdapter:
    """NanoBanana 图片编辑适配器"""

    def __init__(self, api_key: str, base_url: str = "https://api.nanobananaapi.ai"):
        """
        初始化适配器

        Args:
            api_key: NanoBanana API Key
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def process_image(self,
                     image_url: str,
                     prompt: str,
                     poll_interval: int = 2,
                     max_polls: int = 60) -> ProcessingResult:
        """
        处理单张图片

        Args:
            image_url: 图片公开 URL（用户提供的链接）
            prompt: 编辑提示词，如"去除所有文字和水印"
            poll_interval: 轮询间隔（秒）
            max_polls: 最大轮询次数

        Returns:
            ProcessingResult: 处理结果
        """
        try:
            # 1. 提交编辑任务
            task_id = self._submit_task(image_url, prompt)
            if not task_id:
                return ProcessingResult(success=False, message="提交任务失败")

            # 2. 轮询等待结果
            result_url = self._poll_result(task_id, poll_interval, max_polls)
            if not result_url:
                return ProcessingResult(success=False, message="获取结果超时或失败")

            # 3. 下载结果图片
            result_image = self._download_image(result_url)
            if not result_image:
                return ProcessingResult(success=False, message="下载结果图片失败")

            return ProcessingResult(success=True, image=result_image, message="处理成功")

        except Exception as e:
            return ProcessingResult(success=False, message=f"处理失败: {str(e)}")

    def _submit_task(self, image_url: str, prompt: str, reference_image_urls: Optional[list] = None) -> Optional[str]:
        """
        提交编辑任务

        Args:
            image_url: 主图 URL
            prompt: 编辑提示词
            reference_image_urls: 可选的参考图 URL 列表

        Returns:
            task_id 或 None
        """
        url = f"{self.base_url}/api/v1/nanobanana/generate"

        # 构建 imageUrls：参考图在前，主图在后
        all_image_urls = []
        if reference_image_urls:
            all_image_urls.extend(reference_image_urls)
        all_image_urls.append(image_url)

        payload = {
            "type": "IMAGETOIAMGE",
            "prompt": prompt,
            "imageUrls": all_image_urls,
            "callBackUrl": ""  # 空字符串作为占位符
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)

            # 先尝试解析JSON，无论HTTP状态如何
            try:
                data = response.json()
            except:
                data = {}

            # 检查HTTP错误
            if not response.ok:
                error_detail = data.get('message', response.text[:500]) or '无详细错误信息'
                raise Exception(f"HTTP {response.status_code}: {error_detail}")

            # 检查业务错误码
            if data.get("code") == 200:
                return data.get("data", {}).get("taskId")
            else:
                # 显示完整错误信息
                error_code = data.get('code', '?')
                error_msg = data.get('message', '未知错误')
                raise Exception(f"API 错误 (code={error_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            # 网络错误
            raise Exception(f"网络错误: {str(e)}")

    def _poll_result(self,
                    task_id: str,
                    poll_interval: int = 2,
                    max_polls: int = 60) -> Optional[str]:
        """
        轮询任务结果

        Args:
            task_id: 任务 ID
            poll_interval: 轮询间隔（秒）
            max_polls: 最大轮询次数

        Returns:
            结果图片 URL 或 None
        """
        url = f"{self.base_url}/api/v1/nanobanana/record-info"

        for i in range(max_polls):
            response = requests.get(
                url,
                headers=self.headers,
                params={"taskId": task_id},
                timeout=30
            )

            try:
                data = response.json()
            except:
                raise Exception(f"解析响应失败: {response.text[:200]}")

            if not response.ok:
                error_msg = data.get('message', response.text[:500]) or f"HTTP {response.status_code}"
                raise Exception(f"查询任务失败: {error_msg}")

            if data.get("code") != 200:
                error_code = data.get('code', '?')
                error_msg = data.get('message', '未知错误')
                raise Exception(f"查询任务失败 (code={error_code}): {error_msg}")

            task_data = data.get("data", {})
            success_flag = task_data.get("successFlag")

            if success_flag == 1:
                # 成功，获取结果图片 URL
                return task_data.get("response", {}).get("resultImageUrl")
            elif success_flag == 2:
                raise Exception("任务创建失败")
            elif success_flag == 3:
                raise Exception("图片生成失败")
            # success_flag == 0 表示仍在生成中，继续轮询

            time.sleep(poll_interval)

        return None  # 超时

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """
        下载图片

        Args:
            url: 图片 URL

        Returns:
            PIL Image 或 None
        """
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))


def process_with_nanobanana(image_url: str,
                           api_key: str,
                           prompt: Optional[str] = None) -> ProcessingResult:
    """
    便捷函数：使用 NanoBanana 处理图片

    Args:
        image_url: 图片公开 URL
        api_key: NanoBanana API Key
        prompt: 可选的自定义提示词，默认使用通用去文字提示词

    Returns:
        ProcessingResult: 处理结果
    """
    if not prompt:
        prompt = "Enhance this product photo by cleaning up the background."

    adapter = NanoBananaAdapter(api_key)
    return adapter.process_image(image_url, prompt)
