"""
工作流 - 支持多服务商 (NanoBanana / Gemini / LinkAPI.ai)
"""

from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

from PIL import Image

from .config import get_config
from .nanobanana_adapter import NanoBananaAdapter, ProcessingResult
from .gemini_adapter import GeminiAdapter
from .linkapi_adapter import LinkAPIAdapter
from .bananapro_adapter import BananaProAdapter
from .openai_adapter import OpenAIImageAdapter


@dataclass
class BatchResult:
    """批量处理结果"""
    success: bool
    output_path: Optional[str]
    message: str


class TextRemovalWorkflow:
    """文字去除工作流 - 支持多服务商"""

    def __init__(self, api_key: str = None, provider: str = "nanobanana", model: str = None):
        """
        初始化工作流

        Args:
            api_key: API Key，如果为None则从配置文件读取
            provider: 服务商类型，'nanobanana'、'gemini' 或 'linkapi'
            model: 模型名称，如果为None则使用默认值
        """
        self.config = get_config()
        self.provider = provider.lower()
        self.model = model

        # 优先使用传入的 API Key，否则从配置文件读取
        if api_key:
            self.api_key = api_key
        else:
            if self.provider == "gemini":
                self.api_key = self.config.get_gemini_api_key()
            elif self.provider == "linkapi":
                self.api_key = self.config.get_linkapi_api_key()
            elif self.provider == "gpt_image":
                self.api_key = self.config.get_openai_api_key()
            else:
                self.api_key = self.config.get_nanobanana_api_key()

        if not self.api_key or self.api_key in ['your_api_key_here', 'demo_api_key_for_testing']:
            provider_names = {
                "gemini": "Gemini",
                "linkapi": "LinkAPI.ai",
                "bananapro": "BananaPro",
                "nanobanana": "NanoBanana",
                "gpt_image": "OpenAI GPT Image",
            }
            provider_name = provider_names.get(self.provider, "NanoBanana")
            raise ValueError(f"请先在左侧配置面板填写 {provider_name} API Key")

        # 初始化对应适配器
        if self.provider == "gemini":
            # 使用传入的 model 参数或配置中的默认值
            if not self.model:
                gemini_config = self.config.get_gemini_config()
                self.model = gemini_config.get('model', 'gemini-2.5-flash-image')
            self.adapter = GeminiAdapter(self.api_key, self.model)
        elif self.provider == "linkapi":
            # 使用传入的 model 参数或配置中的默认值
            if not self.model:
                linkapi_config = self.config.get_linkapi_config()
                self.model = linkapi_config.get('model', 'gemini-2.5-flash-image')
            self.adapter = LinkAPIAdapter(self.api_key, self.model)
        elif self.provider == "bananapro":
            # 使用传入的 model 参数或配置中的默认值
            if not self.model:
                bp_config = self.config.get_bananapro_config()
                self.model = bp_config.get('model', 'gemini-2.5-flash-image')
            # GUI key 为空时，从 providers.yaml 读取
            if not self.api_key:
                bp_config = self.config.get_bananapro_config()
                self.api_key = bp_config.get('api_key', '')
            self.adapter = BananaProAdapter(self.api_key, self.model)
        elif self.provider == "gpt_image":
            if not self.model:
                oi_config = self.config.get_openai_config()
                self.model = oi_config.get('model', 'gpt-image-2')
            oi_config = self.config.get_openai_config()
            base_url = oi_config.get('base_url', None)
            self.adapter = OpenAIImageAdapter(self.api_key, self.model, base_url=base_url)
        else:
            nb_config = self.config.get_nanobanana_config()
            base_url = nb_config.get('base_url', 'https://api.nanobananaapi.ai')
            self.adapter = NanoBananaAdapter(self.api_key, base_url)

    def process(self,
                image_input: str,
                output_path: str,
                prompt: Optional[str] = None,
                reference_images: Optional[list] = None,
                progress_callback: Optional[Callable[[str, int], None]] = None) -> ProcessingResult:
        """
        处理单张图片

        Args:
            image_input: 图片路径（本地路径或URL）
            output_path: 输出保存路径
            prompt: 可选的自定义编辑提示词
            reference_images: 可选的参考图路径列表（多参考图模式）
            progress_callback: 进度回调函数 (message, progress_percent)

        Returns:
            ProcessingResult: 处理结果
        """
        try:
            # 使用传入的 prompt，不允许为空
            if not prompt:
                return ProcessingResult(
                    success=False,
                    message="未设置提示词，请在界面中输入 Prompt"
                )

            # 根据服务商调用不同处理逻辑
            if self.provider == "gemini":
                return self._process_with_gemini(image_input, output_path, prompt, reference_images, progress_callback)
            elif self.provider == "linkapi":
                return self._process_with_linkapi(image_input, output_path, prompt, reference_images, progress_callback)
            elif self.provider == "bananapro":
                return self._process_with_bananapro(image_input, output_path, prompt, reference_images, progress_callback)
            elif self.provider == "gpt_image":
                return self._process_with_openai(image_input, output_path, prompt, reference_images, progress_callback)
            else:
                return self._process_with_nanobanana(image_input, output_path, prompt, reference_images, progress_callback)

        except Exception as e:
            return ProcessingResult(
                success=False,
                message=f"处理失败: {str(e)}"
            )

    def _process_with_gemini(self,
                            image_path: str,
                            output_path: str,
                            prompt: str,
                            reference_images: Optional[list] = None,
                            progress_callback: Optional[Callable[[str, int], None]] = None) -> ProcessingResult:
        """使用 Gemini 处理"""
        # Gemini 是同步处理，支持本地文件和URL
        result = self.adapter.process_image(image_path, prompt, reference_images=reference_images, progress_callback=progress_callback)

        if not result.success:
            return result

        # 保存结果
        if progress_callback:
            progress_callback("保存结果...", 90)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        output_config = self.config.get_output_config()
        quality = output_config.get('quality', 95)
        fmt = output_config.get('format', 'jpg').upper()

        if fmt == 'JPG' or fmt == 'JPEG':
            result_image = result.image.convert('RGB')
            result_image.save(output_path, quality=quality, optimize=True)
        else:
            result.image.save(output_path, quality=quality)

        if progress_callback:
            progress_callback("完成!", 100)

        return ProcessingResult(
            success=True,
            image=result.image,
            message="处理成功"
        )

    def _process_with_linkapi(self,
                              image_path: str,
                              output_path: str,
                              prompt: str,
                              reference_images: Optional[list] = None,
                              progress_callback: Optional[Callable[[str, int], None]] = None) -> ProcessingResult:
        """使用 LinkAPI.ai 处理"""
        # LinkAPI.ai 是同步处理，支持本地文件
        result = self.adapter.process_image(image_path, prompt, reference_images=reference_images, progress_callback=progress_callback)

        if not result.success:
            return result

        # 保存结果
        if progress_callback:
            progress_callback("保存结果...", 90)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        output_config = self.config.get_output_config()
        quality = output_config.get('quality', 95)
        fmt = output_config.get('format', 'jpg').upper()

        if fmt == 'JPG' or fmt == 'JPEG':
            result_image = result.image.convert('RGB')
            result_image.save(output_path, quality=quality, optimize=True)
        else:
            result.image.save(output_path, quality=quality)

        if progress_callback:
            progress_callback("完成!", 100)

        return ProcessingResult(
            success=True,
            image=result.image,
            message="处理成功"
        )

    def _process_with_bananapro(self,
                                 image_path: str,
                                 output_path: str,
                                 prompt: str,
                                 reference_images: Optional[list] = None,
                                 progress_callback: Optional[Callable[[str, int], None]] = None) -> ProcessingResult:
        """使用 BananaPro 处理"""
        # BananaPro 是同步处理，支持本地文件和URL
        result = self.adapter.process_image(image_path, prompt, reference_images=reference_images, progress_callback=progress_callback)

        if not result.success:
            return result

        # 保存结果
        if progress_callback:
            progress_callback("保存结果...", 90)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        output_config = self.config.get_output_config()
        quality = output_config.get('quality', 95)
        fmt = output_config.get('format', 'jpg').upper()

        if fmt == 'JPG' or fmt == 'JPEG':
            result_image = result.image.convert('RGB')
            result_image.save(output_path, quality=quality, optimize=True)
        else:
            result.image.save(output_path, quality=quality)

        if progress_callback:
            progress_callback("完成!", 100)

        return ProcessingResult(
            success=True,
            image=result.image,
            message="处理成功"
        )

    def _process_with_openai(self,
                              image_path: str,
                              output_path: str,
                              prompt: str,
                              reference_images: Optional[list] = None,
                              progress_callback: Optional[Callable[[str, int], None]] = None) -> ProcessingResult:
        """使用 OpenAI GPT Image 处理"""
        result = self.adapter.process_image(image_path, prompt, reference_images=reference_images, progress_callback=progress_callback)

        if not result.success:
            return result

        if progress_callback:
            progress_callback("保存结果...", 90)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        output_config = self.config.get_output_config()
        quality = output_config.get('quality', 95)
        fmt = output_config.get('format', 'jpg').upper()

        if fmt == 'JPG' or fmt == 'JPEG':
            result_image = result.image.convert('RGB')
            result_image.save(output_path, quality=quality, optimize=True)
        else:
            result.image.save(output_path, quality=quality)

        if progress_callback:
            progress_callback("完成!", 100)

        return ProcessingResult(
            success=True,
            image=result.image,
            message="处理成功"
        )

    def _process_with_nanobanana(self,
                                image_path: str,
                                output_path: str,
                                prompt: str,
                                reference_images: Optional[list] = None,
                                progress_callback: Optional[Callable[[str, int], None]] = None) -> ProcessingResult:
        """使用 NanoBanana 处理"""
        # 检查是否是本地文件路径
        from pathlib import Path
        if Path(image_path).exists():
            return ProcessingResult(
                success=False,
                message="NanoBanana 不支持本地文件，请使用图片URL或切换到 Google Gemini"
            )

        # NanoBanana 参考图需要是URL，过滤掉非URL的参考图
        ref_urls = None
        if reference_images:
            ref_urls = [ref for ref in reference_images if ref.startswith('http')]
            if not ref_urls:
                ref_urls = None

        # 获取轮询配置
        poll_interval, max_polls = self.config.get_poll_config()

        # 提交任务
        if progress_callback:
            progress_callback("提交编辑任务...", 10)

        try:
            task_id = self.adapter._submit_task(image_path, prompt, reference_image_urls=ref_urls)
            if not task_id:
                return ProcessingResult(success=False, message="提交任务失败")
        except Exception as e:
            return ProcessingResult(success=False, message=f"提交任务失败: {str(e)}")

        # 轮询等待结果
        if progress_callback:
            progress_callback("正在处理中...", 30)

        result_url = self.adapter._poll_result(task_id, poll_interval, max_polls)
        if not result_url:
            return ProcessingResult(success=False, message="获取结果超时或失败")

        # 下载结果
        if progress_callback:
            progress_callback("下载结果...", 80)

        result_image = self.adapter._download_image(result_url)
        if not result_image:
            return ProcessingResult(success=False, message="下载结果图片失败")

        # 保存结果
        if progress_callback:
            progress_callback("保存结果...", 90)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        output_config = self.config.get_output_config()
        quality = output_config.get('quality', 95)
        fmt = output_config.get('format', 'jpg').upper()

        if fmt == 'JPG' or fmt == 'JPEG':
            result_image = result_image.convert('RGB')
            result_image.save(output_path, quality=quality, optimize=True)
        else:
            result_image.save(output_path, quality=quality)

        if progress_callback:
            progress_callback("完成!", 100)

        return ProcessingResult(
            success=True,
            image=result_image,
            message="处理成功"
        )

    def batch_process(self,
                      image_urls: list,
                      output_dir: str,
                      prompt: Optional[str] = None,
                      progress_callback: Optional[Callable[[str, int, int], None]] = None) -> list:
        """
        批量处理图片

        Args:
            image_urls: 图片 URL 列表
            output_dir: 输出目录
            prompt: 可选的自定义编辑提示词
            progress_callback: 进度回调 (current_url, current_index, total)

        Returns:
            List[ProcessingResult]: 所有处理结果
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []
        total = len(image_urls)

        for idx, url in enumerate(image_urls, 1):
            # 构建输出文件名
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                filename = Path(parsed.path).stem or f"image_{idx}"
            except:
                filename = f"image_{idx}"

            out_file = output_path / f"{filename}_clean.jpg"

            def single_progress(msg, pct):
                if progress_callback:
                    progress_callback(f"[{idx}/{total}] {msg}", idx, total)

            result = self.process(url, str(out_file), prompt, single_progress)
            results.append(result)

            # 添加延迟避免 API 限制
            if idx < total:
                import time
                time.sleep(1)

        return results
