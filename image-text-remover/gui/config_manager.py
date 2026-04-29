"""
GUI配置管理器 - 保存和加载用户配置（简化版 - NanoBanana）
"""

import json
import base64
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict


@dataclass
class GUIConfig:
    """简化版 GUI 配置"""
    # 服务商选择
    provider: str = "Google Gemini"  # "NanoBanana" 或 "Google Gemini"
    # API Key (加密存储)
    api_key: str = ""
    # 编辑提示词（安全措辞，避免触发API内容安全）
    prompt: str = "Enhance this product photo by cleaning up the background."
    # 输出质量
    output_quality: int = 95
    # 输出格式
    output_format: str = "jpg"
    # 默认模型
    default_model: str = "gemini-2.5-flash-image"
    # 提示词模板
    prompt_templates: Dict[str, str] = field(default_factory=dict)
    # 当前选中的模板
    selected_template: str = ""


class GUIConfigManager:
    """GUI配置管理器 - 简化版"""

    CONFIG_FILE = Path("config/settings.json")

    # 默认提示词模板（首次运行时自动加载，之后可自由修改）
    DEFAULT_TEMPLATES = {
        "通用去水印": "Enhance this product photo by cleaning up the background.",
        "去除品牌标识": "Clean up this image by restoring it to its original clean state.",
        "产品图优化": "Enhance this product photo with a clean, professional look.",
        "清空背景文字": "Remove all text and characters from the background. Keep the main subject completely unchanged.",
    }

    # 可用模型选项
    MODEL_OPTIONS = {
        "gemini-2.5-flash-image": "Nano Banana",
        "gemini-3.1-flash-image-preview": "Nano Banana 2",
        "gemini-3-pro-image-preview": "Nano Banana Pro"
    }

    # 安全提示词（避免 watermark/logo/signature 等触发API内容安全）
    SAFE_PROMPT = "Enhance this product photo by cleaning up the background."

    def __init__(self):
        self.provider = "BananaPro"
        self.api_key = ""
        self.prompt = self.SAFE_PROMPT
        self.output_quality = 95
        self.output_format = "jpg"
        self.default_model = "gemini-2.5-flash-image"
        self.prompt_templates: Dict[str, str] = {}  # 用户自定义模板
        self.selected_template: str = ""  # 当前选中的模板

        self._ensure_config_dir()
        self.load()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _encrypt(self, text: str) -> str:
        """简单加密（base64）"""
        if not text:
            return ""
        return base64.b64encode(text.encode()).decode()

    def _decrypt(self, text: str) -> str:
        """简单解密"""
        if not text:
            return ""
        try:
            return base64.b64decode(text.encode()).decode()
        except:
            return text

    def save(self):
        """保存配置到文件"""
        config = {
            "provider": self.provider,
            "api_key": self._encrypt(self.api_key),
            "prompt": self.prompt,
            "output_quality": self.output_quality,
            "output_format": self.output_format,
            "default_model": self.default_model,
            "prompt_templates": self.prompt_templates,
            "selected_template": self.selected_template,
        }

        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def load(self):
        """从文件加载配置"""
        if not self.CONFIG_FILE.exists():
            # 首次运行，加载默认模板到用户模板
            self._init_default_templates()
            self.save()
            return

        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 加载配置
            self.provider = config.get("provider", "Google Gemini")
            self.api_key = self._decrypt(config.get("api_key", ""))
            self.prompt = config.get("prompt", self.prompt)
            self.output_quality = config.get("output_quality", 95)
            self.output_format = config.get("output_format", "jpg")
            self.default_model = config.get("default_model", "gemini-2.5-flash-image")
            self.prompt_templates = config.get("prompt_templates", {})
            self.selected_template = config.get("selected_template", "")

            # 如果是旧版本配置没有模板数据，初始化默认模板
            if not self.prompt_templates:
                self._init_default_templates()
                self.save()

        except Exception as e:
            print(f"加载配置失败: {e}，使用默认配置")
            self._init_default_templates()
            self.save()

    def _init_default_templates(self):
        """初始化默认模板到用户模板"""
        self.prompt_templates = dict(self.DEFAULT_TEMPLATES)

    def update(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()

    # ============ 模板管理方法 ============

    def get_all_templates(self) -> Dict[str, str]:
        """获取所有模板（所有模板都存储在 prompt_templates 中）"""
        return dict(self.prompt_templates)

    def get_template_names(self) -> list:
        """获取所有模板名称列表"""
        return list(self.prompt_templates.keys())

    def get_template_content(self, name: str) -> str:
        """获取指定模板的提示词内容"""
        all_templates = self.get_all_templates()
        return all_templates.get(name, "")

    def is_default_template(self, name: str) -> bool:
        """检查是否为默认模板（不可修改）"""
        return name in self.DEFAULT_TEMPLATES

    def save_template(self, name: str, prompt: str) -> bool:
        """保存新模板或更新现有模板

        Args:
            name: 模板名称
            prompt: 提示词内容

        Returns:
            bool: 是否保存成功
        """
        if not name or not name.strip():
            return False

        name = name.strip()
        self.prompt_templates[name] = prompt
        self.save()
        return True

    def delete_template(self, name: str) -> bool:
        """删除自定义模板

        Args:
            name: 模板名称

        Returns:
            bool: 是否删除成功
        """
        if name in self.prompt_templates:
            del self.prompt_templates[name]
            # 如果删除的是当前选中的模板，清空选中状态
            if self.selected_template == name:
                self.selected_template = ""
            self.save()
            return True
        return False

    def update_template(self, old_name: str, new_name: str, new_prompt: str) -> bool:
        """更新模板（重命名或修改内容）

        Args:
            old_name: 原模板名称
            new_name: 新模板名称
            new_prompt: 新提示词内容

        Returns:
            bool: 是否更新成功
        """
        if not new_name or not new_name.strip():
            return False

        new_name = new_name.strip()

        # 如果名称变化，先删除旧的
        if old_name in self.prompt_templates:
            del self.prompt_templates[old_name]

        self.prompt_templates[new_name] = new_prompt

        # 更新选中状态
        if self.selected_template == old_name:
            self.selected_template = new_name

        self.save()
        return True
