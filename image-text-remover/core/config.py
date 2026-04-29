"""
配置管理模块
统一读取 providers.yaml 配置
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PromptConfig:
    """Prompt配置"""
    positive: str
    negative: str


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "providers.yaml"):
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()

    def _load_config(self):
        """加载YAML配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """获取服务商配置"""
        providers = self._config.get('providers', {})
        if provider_name not in providers:
            raise ValueError(f"未找到服务商配置: {provider_name}")
        return providers[provider_name]

    def get_default_provider(self, service_type: str) -> str:
        """获取默认服务商"""
        key = f'default_{service_type}'
        return self._config.get(key, '')

    def get_prompt_strategy(self) -> str:
        """获取prompt策略 (auto/universal)"""
        ecommerce = self._config.get('ecommerce', {})
        return ecommerce.get('prompt_strategy', 'auto')

    def get_universal_prompt(self) -> PromptConfig:
        """获取通用prompt"""
        ecommerce = self._config.get('ecommerce', {})
        universal = ecommerce.get('universal_prompt', {})

        # 默认prompt（当配置为空时使用）
        default_positive = "product photography, clean background, professional studio lighting, seamless texture, commercial catalog style, high quality, sharp focus"
        default_negative = "text, watermark, logo, brand name, signature, caption, letters, words, slogan, price tag, qr code, blurry, low quality, distorted"

        positive = universal.get('positive', '') or default_positive
        negative = universal.get('negative', '') or default_negative

        return PromptConfig(
            positive=positive,
            negative=negative
        )

    def get_scene_prompt(self, scene: str) -> PromptConfig:
        """获取场景专用prompt"""
        ecommerce = self._config.get('ecommerce', {})
        prompts = ecommerce.get('inpaint_prompts', {})

        if scene not in prompts:
            scene = 'default'

        scene_config = prompts.get(scene, {})
        return PromptConfig(
            positive=scene_config.get('positive', ''),
            negative=scene_config.get('negative', '')
        )

    def get_blocklist(self) -> list:
        """获取屏蔽词列表"""
        ecommerce = self._config.get('ecommerce', {})
        return ecommerce.get('blocklist', [])

    def get_output_config(self) -> Dict[str, Any]:
        """获取输出配置"""
        return self._config.get('output', {})

    def get_ecommerce_config(self) -> Dict[str, Any]:
        """获取电商配置"""
        return self._config.get('ecommerce', {})

    # ==================== NanoBanana 配置 ====================

    def get_nanobanana_config(self) -> Dict[str, Any]:
        """获取 NanoBanana 配置"""
        return self._config.get('providers', {}).get('nanobanana', {})

    def get_nanobanana_api_key(self) -> str:
        """获取 NanoBanana API Key"""
        config = self.get_nanobanana_config()
        return config.get('api_key', '')

    # ==================== Gemini 配置 ====================

    def get_gemini_config(self) -> Dict[str, Any]:
        """获取 Gemini 配置"""
        return self._config.get('providers', {}).get('gemini', {})

    def get_gemini_api_key(self) -> str:
        """获取 Gemini API Key"""
        config = self.get_gemini_config()
        return config.get('api_key', '')

    # ==================== LinkAPI.ai 配置 ====================

    def get_linkapi_config(self) -> Dict[str, Any]:
        """获取 LinkAPI.ai 配置"""
        return self._config.get('providers', {}).get('linkapi', {})

    def get_linkapi_api_key(self) -> str:
        """获取 LinkAPI.ai API Key"""
        config = self.get_linkapi_config()
        return config.get('api_key', '')

    # ==================== BananaPro 配置 ====================

    def get_bananapro_config(self) -> Dict[str, Any]:
        """获取 BananaPro 配置"""
        return self._config.get('providers', {}).get('bananapro', {})

    def get_bananapro_api_key(self) -> str:
        """获取 BananaPro API Key"""
        config = self.get_bananapro_config()
        return config.get('api_key', '')

    # ==================== OpenAI GPT Image 配置 ====================

    def get_openai_config(self) -> Dict[str, Any]:
        """获取 OpenAI GPT Image 配置"""
        return self._config.get('providers', {}).get('openai_image', {})

    def get_openai_api_key(self) -> str:
        """获取 OpenAI API Key"""
        config = self.get_openai_config()
        return config.get('api_key', '')

    def get_processing_config(self) -> Dict[str, Any]:
        """获取处理参数配置"""
        return self._config.get('processing', {})

    def get_default_prompt(self) -> str:
        """获取默认编辑提示词"""
        config = self.get_processing_config()
        return config.get('prompt', 'Enhance this product photo by cleaning up the background.')

    def get_poll_config(self) -> tuple:
        """获取轮询配置 (interval, max_polls)"""
        config = self.get_processing_config()
        return (
            config.get('poll_interval', 2),
            config.get('max_polls', 60)
        )


# 全局配置实例
_config_instance = None


def get_config() -> ConfigManager:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
