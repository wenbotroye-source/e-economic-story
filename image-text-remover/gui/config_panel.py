"""
配置面板 - 左侧API和参数配置（简化版 - 只使用 NanoBanana）
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from .config_manager import GUIConfigManager
from .template_manager import TemplateManagerDialog


class ConfigPanel(ttk.LabelFrame):
    """配置面板 - NanoBanana 简化版"""

    def __init__(self, master, config_manager: GUIConfigManager, on_template_change=None):
        super().__init__(master, text="配置", padding=10)
        self.config = config_manager
        self.on_template_change = on_template_change  # 模板变化回调

        self._create_api_section()
        self._create_separator()
        self._create_prompt_section()
        self._create_separator()
        self._create_output_section()

        # 加载保存的配置
        self._load_config()

    def _create_api_section(self):
        """创建API配置区域"""
        api_frame = ttk.LabelFrame(self, text="API 配置", padding=5)
        api_frame.pack(fill="x", pady=5)

        # 服务商选择
        ttk.Label(api_frame, text="服务商:").grid(row=0, column=0, sticky="w", pady=2)
        self.provider = ttk.Combobox(api_frame, state="readonly", width=25)
        self.provider['values'] = ("NanoBanana", "Google Gemini", "LinkAPI.ai", "BananaPro", "OpenAI GPT Image")
        self.provider.set("BananaPro")  # 默认选择 BananaPro
        self.provider.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.provider.bind("<<ComboboxSelected>>", self._on_provider_change)

        # API Key
        ttk.Label(api_frame, text="API Key:").grid(row=1, column=0, sticky="w", pady=2)
        self.api_key = ttk.Entry(api_frame, show="*", width=30)
        self.api_key.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        # 显示/隐藏按钮
        self.show_key = tk.BooleanVar(value=False)
        ttk.Checkbutton(api_frame, text="显示", variable=self.show_key,
                       command=self._toggle_key).grid(row=1, column=2)

        # 提示信息
        self.api_hint = ttk.Label(api_frame, text="使用 Google Gemini API Key",
                 font=("Arial", 8), foreground="gray")
        self.api_hint.grid(row=2, column=0, columnspan=3, sticky="w", pady=2)

        api_frame.columnconfigure(1, weight=1)

    def _create_prompt_section(self):
        """创建Prompt配置区域"""
        self.prompt_frame = ttk.LabelFrame(self, text="编辑提示词 (Prompt)", padding=5)
        self.prompt_frame.pack(fill="both", expand=True, pady=5)

        # 模板选择行
        template_frame = ttk.Frame(self.prompt_frame)
        template_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(template_frame, text="模板:").pack(side="left")

        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(
            template_frame,
            textvariable=self.template_var,
            state="readonly",
            width=15
        )
        self.template_combo.pack(side="left", padx=5)
        self.template_combo.bind("<<ComboboxSelected>>", self._on_template_select)

        ttk.Button(template_frame, text="保存为模板",
                  command=self._save_as_template).pack(side="left", padx=2)
        ttk.Button(template_frame, text="更新当前模板",
                  command=self._update_current_template).pack(side="left", padx=2)
        ttk.Button(template_frame, text="删除",
                  command=self._delete_template).pack(side="left", padx=2)
        ttk.Button(template_frame, text="管理",
                  command=self._manage_templates).pack(side="left", padx=2)

        # Prompt 说明
        ttk.Label(self.prompt_frame,
                 text="描述你想要的编辑效果（英文效果更好）：",
                 font=("Arial", 8), foreground="gray").pack(anchor="w")

        # Prompt 输入框
        self.prompt = tk.Text(self.prompt_frame, height=8, wrap="word")
        self.prompt.pack(fill="both", expand=True, pady=2)

    def _create_output_section(self):
        """创建输出配置区域"""
        output_frame = ttk.LabelFrame(self, text="输出配置", padding=5)
        output_frame.pack(fill="x", pady=5)

        # 输出质量
        ttk.Label(output_frame, text="输出质量:").grid(row=0, column=0, sticky="w", pady=2)
        quality_frame = ttk.Frame(output_frame)
        quality_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        self.output_quality = tk.IntVar(value=95)
        quality_scale = ttk.Scale(quality_frame, from_=50, to=100, orient="horizontal",
                                  variable=self.output_quality)
        quality_scale.pack(side="left", fill="x", expand=True)
        self.quality_label = ttk.Label(quality_frame, text="95%")
        self.quality_label.pack(side="left", padx=5)

        # 质量标签更新
        self.output_quality.trace("w", lambda *args: self.quality_label.config(
            text=f"{self.output_quality.get()}%"))

        # 输出格式
        ttk.Label(output_frame, text="输出格式:").grid(row=1, column=0, sticky="w", pady=2)
        self.output_format = ttk.Combobox(output_frame, state="readonly", width=10)
        self.output_format['values'] = ("jpg", "png", "webp")
        self.output_format.set("jpg")
        self.output_format.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        output_frame.columnconfigure(1, weight=1)

    def _create_separator(self):
        """创建分隔线"""
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

    def _toggle_key(self):
        """切换API Key显示"""
        if self.show_key.get():
            self.api_key.config(show="")
        else:
            self.api_key.config(show="*")

    def _on_provider_change(self, event=None):
        """服务商切换事件"""
        provider = self.provider.get()
        if provider == "Google Gemini":
            self.api_hint.config(text="使用 Google AI Studio API Key (aistudio.google.com)")
        elif provider == "NanoBanana":
            self.api_hint.config(text="使用 NanoBanana API Key (nanobanana.com)")
        elif provider == "LinkAPI.ai":
            self.api_hint.config(text="使用 LinkAPI.ai API Key (linkapi.ai)")
        elif provider == "OpenAI GPT Image":
            self.api_hint.config(text="使用 OpenAI API Key (platform.openai.com)")
        else:  # BananaPro
            self.api_hint.config(text="NanoBanana PRO (own-jarvis-api.com)")
            # 从 providers.yaml 读取默认 API Key
            if not self.api_key.get().strip():
                try:
                    from core.config import get_config
                    bp_config = get_config().get_bananapro_config()
                    default_key = bp_config.get('api_key', '')
                    if default_key:
                        self.api_key.delete(0, "end")
                        self.api_key.insert(0, default_key)
                except:
                    pass

    def _refresh_template_list(self):
        """刷新模板下拉列表"""
        template_names = self.config.get_template_names()
        self.template_combo['values'] = template_names

    def _on_template_select(self, event=None):
        """模板选择事件"""
        selected = self.template_var.get()
        if selected:
            prompt_content = self.config.get_template_content(selected)
            if prompt_content:
                self.prompt.delete("1.0", "end")
                self.prompt.insert("1.0", prompt_content)
                self.config.selected_template = selected
                self.config.save()

    def _save_as_template(self):
        """将当前提示词保存为模板"""
        current_prompt = self.prompt.get("1.0", "end-1c").strip()
        if not current_prompt:
            messagebox.showwarning("警告", "当前提示词为空，无法保存")
            return

        # 弹出输入框询问模板名称
        name = simpledialog.askstring(
            "保存模板",
            "请输入模板名称：",
            parent=self
        )

        if not name:
            return

        name = name.strip()

        # 检查是否已存在（所有模板都存储在 prompt_templates 中）
        if name in self.config.get_template_names():
            if not messagebox.askyesno(
                "确认",
                f"模板 '{name}' 已存在，是否覆盖？"
            ):
                return

        # 保存模板
        if self.config.save_template(name, current_prompt):
            self._refresh_template_list()
            self.template_var.set(name)
            # 通知主窗口模板已变化
            if self.on_template_change:
                self.on_template_change()
            messagebox.showinfo("成功", f"模板 '{name}' 已保存")
        else:
            messagebox.showerror("错误", "保存模板失败")

    def _update_current_template(self):
        """更新当前选中的模板（用编辑框的内容覆盖）"""
        current_template = self.template_var.get()

        if not current_template:
            messagebox.showwarning("警告", "请先选择一个模板")
            return

        current_prompt = self.prompt.get("1.0", "end-1c").strip()
        if not current_prompt:
            messagebox.showwarning("警告", "当前提示词为空，无法保存")
            return

        # 确认更新
        if messagebox.askyesno(
            "确认更新",
            f"确定要更新模板 '{current_template}' 的内容吗？\n"
            "这将覆盖原模板内容。"
        ):
            if self.config.save_template(current_template, current_prompt):
                messagebox.showinfo("成功", f"模板 '{current_template}' 已更新")
            else:
                messagebox.showerror("错误", "更新模板失败")

    def _delete_template(self):
        """删除当前选中的模板（默认模板不可删除）"""
        current_template = self.template_var.get()

        if not current_template:
            messagebox.showwarning("警告", "请先选择一个模板")
            return

        # 检查是否为默认模板
        if self.config.is_default_template(current_template):
            messagebox.showwarning(
                "无法删除",
                f"'{current_template}' 是默认模板，不能删除。\n"
                "你可以在模板管理器中重命名或修改内容。"
            )
            return

        # 确认删除
        if messagebox.askyesno("确认删除", f"确定要删除模板 '{current_template}' 吗？"):
            if self.config.delete_template(current_template):
                self._refresh_template_list()
                self.template_var.set("")
                self.config.selected_template = ""
                self.config.save()
                # 通知主窗口模板已变化
                if self.on_template_change:
                    self.on_template_change()
                messagebox.showinfo("成功", f"模板 '{current_template}' 已删除")
            else:
                messagebox.showerror("错误", "删除模板失败")

    def _manage_templates(self):
        """打开模板管理对话框"""
        # 记录对话框打开前的模板数量
        templates_before = set(self.config.get_template_names())

        dialog = TemplateManagerDialog(self, self.config)
        self.wait_window(dialog)

        # 对话框关闭后刷新列表
        self._refresh_template_list()

        # 如果当前选中的模板被删除了，清空选择
        if self.config.selected_template not in self.config.get_template_names():
            self.template_var.set("")

        # 检查模板是否有变化（新增、删除、重命名）
        templates_after = set(self.config.get_template_names())
        if templates_before != templates_after:
            # 通知主窗口模板已变化
            if self.on_template_change:
                self.on_template_change()

    def _load_config(self):
        """加载配置到界面"""
        # 服务商
        self.provider.set(self.config.provider)
        self._on_provider_change()  # 更新提示文本

        # API Key
        self.api_key.delete(0, "end")
        self.api_key.insert(0, self.config.api_key)

        # 输出配置
        self.output_quality.set(self.config.output_quality)
        self.output_format.set(self.config.output_format)

        # 刷新模板列表
        self._refresh_template_list()

        # Prompt 配置
        self.prompt.delete("1.0", "end")
        self.prompt.insert("1.0", self.config.prompt)

        # 恢复上次选中的模板
        if self.config.selected_template:
            self.template_var.set(self.config.selected_template)

    def save_config(self):
        """保存配置"""
        # 更新配置
        self.config.provider = self.provider.get()
        self.config.api_key = self.api_key.get()
        self.config.output_quality = self.output_quality.get()
        self.config.output_format = self.output_format.get()
        self.config.prompt = self.prompt.get("1.0", "end-1c")

        self.config.save()

    def get_config_dict(self):
        """获取配置字典（用于工作流）"""
        self.save_config()

        # 转换服务商名称为内部标识
        provider_map = {
            "NanoBanana": "nanobanana",
            "Google Gemini": "gemini",
            "LinkAPI.ai": "linkapi",
            "BananaPro": "bananapro",
            "OpenAI GPT Image": "gpt_image",
        }
        provider = provider_map.get(self.provider.get(), "gemini")

        return {
            "provider": provider,
            "api_key": self.api_key.get(),
            "prompt": self.prompt.get("1.0", "end-1c"),
            "output_quality": self.output_quality.get(),
            "output_format": self.output_format.get(),
        }
