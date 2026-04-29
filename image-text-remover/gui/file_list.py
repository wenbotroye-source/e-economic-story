"""
文件列表组件 - 显示待处理的图片列表，支持每图选择模型
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import List, Callable, Optional
from dataclasses import dataclass, field


@dataclass
class FileListItem:
    """文件项数据结构"""
    file_path: str
    filename: str
    status: str = "等待"
    model: str = "gemini-3-pro-image-preview"  # 默认模型
    prompt: str = ""  # 每图独立的提示词
    message: str = ""
    is_reference: bool = False  # 是否为参考图


class FileList(ttk.LabelFrame):
    """文件列表组件 - 带模型选择"""

    STATUS_WAITING = "等待"
    STATUS_PROCESSING = "处理中"
    STATUS_DONE = "完成"
    STATUS_ERROR = "失败"

    # 模型选项映射
    MODEL_OPTIONS = {
        "gemini-2.5-flash-image": "Nano Banana",
        "gemini-3.1-flash-image-preview": "BananaPro 2",
        "gemini-3-pro-image-preview": "BananaPro Pro",
        "gpt-image-2": "OpenAI GPT Image"
    }

    def __init__(self, master, on_selection_change: Optional[Callable] = None):
        super().__init__(master, text="待处理文件", padding=5)
        self.on_selection_change = on_selection_change

        # 文件数据 {path: FileListItem}
        self.files: dict[str, FileListItem] = {}
        # 每行对应的 widget 引用 {path: frame}
        self._row_widgets: dict[str, dict] = {}

        # 默认模型
        self.default_model = "gemini-3-pro-image-preview"

        # 模板选项
        self._template_options: dict[str, str] = {}  # 模板名称 -> 提示词内容
        self._default_template: str = ""  # 默认模板名称
        self._template_name_to_display: dict[str, str] = {}  # 模板名称 -> 显示文本

        self._create_toolbar()
        self._create_list_container()

    def _create_list_container(self):
        """创建列表容器（带滚动条）"""
        # 创建 Canvas 和滚动条（垂直 + 水平）
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=scrollbar.set, xscrollcommand=h_scrollbar.set)

        # 创建内容框架
        self.list_frame = ttk.Frame(self.canvas)

        # 绑定滚动
        self.list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # 在 Canvas 中创建窗口（固定最小宽度，确保所有列可见）
        self.canvas_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        # 绑定 Canvas 大小变化
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 布局
        self.canvas.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")

        # 标题行
        self._create_header()

    def _on_canvas_configure(self, event):
        """Canvas 大小变化时调整内部窗口宽度"""
        # 不强制宽度，允许内容比Canvas宽，由水平滚动条控制
        pass

    def _create_header(self):
        """创建列表标题行"""
        header = ttk.Frame(self.list_frame)
        header.pack(fill="x", pady=(0, 5))

        ttk.Label(header, text="状态", width=6).pack(side="left")
        ttk.Label(header, text="文件名", width=20).pack(side="left", padx=5)
        ttk.Label(header, text="复用参考", width=7).pack(side="left", padx=2)
        ttk.Label(header, text="提示词模板", width=14).pack(side="left", padx=2)
        ttk.Label(header, text="模型", width=14).pack(side="left", padx=2)
        ttk.Label(header, text="", width=3).pack(side="left")  # 删除按钮列

        # 分隔线
        ttk.Separator(self.list_frame, orient="horizontal").pack(fill="x", pady=2)

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self)
        toolbar.pack(side="bottom", fill="x", padx=5, pady=5)

        # 第一行 - 操作按钮
        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(fill="x", pady=2)

        ttk.Button(btn_frame, text="添加图片", command=self.add_files_dialog).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="添加文件夹", command=self.add_folder_dialog).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="删除选中", command=self.remove_selected).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="清空列表", command=self.clear).pack(side="left", padx=2)

        # 第二行 - 默认模型选择
        model_frame = ttk.Frame(toolbar)
        model_frame.pack(fill="x", pady=2)

        ttk.Label(model_frame, text="默认模型:").pack(side="left")

        # 创建显示名称到key的映射
        self._display_to_key = {v: k for k, v in self.MODEL_OPTIONS.items()}
        self._key_to_display = self.MODEL_OPTIONS.copy()

        self.default_model_var = tk.StringVar(value=self._key_to_display.get("gemini-3-pro-image-preview", "BananaPro Pro"))
        default_model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.default_model_var,
            values=list(self.MODEL_OPTIONS.values()),  # 使用显示名称
            width=25,
            state="readonly"
        )
        default_model_combo.pack(side="left", padx=5)
        default_model_combo.bind("<<ComboboxSelected>>", self._on_default_model_change)

    def _on_default_model_change(self, event=None):
        """默认模型改变"""
        display_name = self.default_model_var.get()
        self.default_model = self._display_to_key.get(display_name, "gemini-3-pro-image-preview")

    def _get_status_color(self, status: str) -> str:
        """获取状态颜色"""
        colors = {
            self.STATUS_WAITING: "gray",
            self.STATUS_PROCESSING: "blue",
            self.STATUS_DONE: "green",
            self.STATUS_ERROR: "red",
        }
        return colors.get(status, "black")

    def _create_file_row(self, item: FileListItem) -> dict:
        """创建文件行，返回 widget 引用字典"""
        row = ttk.Frame(self.list_frame)
        row.pack(fill="x", pady=1)

        # 状态标签
        status_label = ttk.Label(row, text=item.status, width=6, foreground=self._get_status_color(item.status))
        status_label.pack(side="left")

        # 文件名（带悬停提示完整路径）
        name_label = ttk.Label(row, text=item.filename, width=20, cursor="hand2")
        name_label.pack(side="left", padx=5)
        name_label.bind("<Double-1>", lambda e: self._preview_image(item.file_path))

        # 参考图复选框
        ref_var = tk.BooleanVar(value=item.is_reference)

        def on_ref_toggle():
            item.is_reference = ref_var.get()
            # 视觉反馈：参考图的文件名变为斜体紫色
            if item.is_reference:
                name_label.config(font=("TkDefaultFont", 9, "italic"), foreground="purple")
            else:
                name_label.config(font=("TkDefaultFont", 9, "normal"), foreground="black")

        ref_check = tk.Checkbutton(row, variable=ref_var, command=on_ref_toggle)
        ref_check.pack(side="left", padx=2)

        # 模板选择下拉框
        template_var = tk.StringVar(value="使用全局配置")
        template_combo = ttk.Combobox(
            row,
            textvariable=template_var,
            width=14,
            state="readonly"
        )
        # 设置模板选项（如果已配置）
        template_names = ["使用全局配置"] + list(self._template_options.keys())
        template_combo["values"] = template_names
        # 如果有默认模板，选中它
        if self._default_template and self._default_template in self._template_options:
            template_var.set(self._default_template)
            item.prompt = self._template_options[self._default_template]
        template_combo.pack(side="left", padx=2)

        # 绑定模板选择事件
        def on_template_change(event):
            template_name = template_var.get()
            if template_name == "使用全局配置":
                item.prompt = ""
            else:
                item.prompt = self._template_options.get(template_name, "")

        template_combo.bind("<<ComboboxSelected>>", on_template_change)

        # 模型选择下拉框（显示友好名称）
        model_var = tk.StringVar(value=self._key_to_display.get(item.model, item.model))
        model_combo = ttk.Combobox(
            row,
            textvariable=model_var,
            values=list(self.MODEL_OPTIONS.values()),
            width=14,
            state="readonly"
        )
        model_combo.pack(side="left", padx=2)

        # 绑定模型选择事件
        def on_model_change(event):
            display_name = model_var.get()
            item.model = self._display_to_key.get(display_name, item.model)

        model_combo.bind("<<ComboboxSelected>>", on_model_change)

        # 删除按钮
        del_btn = ttk.Button(row, text="×", width=2,
                            command=lambda: self.remove_file(item.file_path))
        del_btn.pack(side="left", padx=2)

        return {
            "frame": row,
            "status_label": status_label,
            "name_label": name_label,
            "ref_var": ref_var,
            "ref_check": ref_check,
            "template_combo": template_combo,
            "template_var": template_var,
            "model_combo": model_combo,
            "model_var": model_var,
            "del_btn": del_btn
        }

    def add_file(self, file_path: str) -> bool:
        """添加单个文件"""
        path = Path(file_path)

        # 检查文件类型
        if path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.webp']:
            return False

        # 检查是否已存在
        if str(path) in self.files:
            return False

        # 创建文件项
        item = FileListItem(
            file_path=str(path),
            filename=path.name,
            model=self.default_model
        )

        # 添加到数据字典
        self.files[str(path)] = item

        # 创建行 UI
        widgets = self._create_file_row(item)
        self._row_widgets[str(path)] = widgets

        return True

    def add_files(self, file_paths: List[str]):
        """添加多个文件"""
        for path in file_paths:
            self.add_file(path)

    def add_files_dialog(self):
        """打开文件选择对话框"""
        from tkinter import filedialog
        files = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.webp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("WebP", "*.webp"),
                ("所有文件", "*.*")
            ]
        )
        self.add_files(list(files))

    def add_folder_dialog(self):
        """打开文件夹选择对话框"""
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            path = Path(folder)
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                for file in path.glob(ext):
                    self.add_file(str(file))
                for file in path.glob(ext.upper()):
                    self.add_file(str(file))

    def remove_file(self, file_path: str):
        """删除单个文件"""
        if file_path in self._row_widgets:
            self._row_widgets[file_path]["frame"].destroy()
            del self._row_widgets[file_path]
        if file_path in self.files:
            del self.files[file_path]

    def remove_selected(self):
        """删除选中的文件（当前实现为删除第一个，可扩展为多选）"""
        if self.files:
            # 删除第一个文件（简单实现）
            first_key = next(iter(self.files))
            self.remove_file(first_key)

    def clear(self):
        """清空列表"""
        for widgets in self._row_widgets.values():
            widgets["frame"].destroy()
        self._row_widgets.clear()
        self.files.clear()

    def update_status(self, file_path: str, status: str, message: str = ""):
        """更新文件状态"""
        if file_path not in self.files:
            return

        item = self.files[file_path]
        item.status = status
        if message:
            item.message = message

        # 更新 UI
        if file_path in self._row_widgets:
            widgets = self._row_widgets[file_path]
            widgets["status_label"].config(
                text=status,
                foreground=self._get_status_color(status)
            )

    def update_message(self, file_path: str, message: str):
        """更新文件消息"""
        if file_path in self.files:
            self.files[file_path].message = message

    def get_files(self) -> List[FileListItem]:
        """获取所有文件项（包含模型信息）"""
        return list(self.files.values())

    def get_file_paths(self) -> List[str]:
        """获取所有文件路径"""
        return list(self.files.keys())

    def get_waiting_files(self) -> List[FileListItem]:
        """获取等待处理的文件（排除参考图）"""
        return [item for item in self.files.values()
                if item.status == self.STATUS_WAITING and not item.is_reference]

    def get_reference_files(self) -> List[FileListItem]:
        """获取标记为参考图的文件"""
        return [item for item in self.files.values() if item.is_reference]

    def set_default_model(self, model: str):
        """设置默认模型（传入模型key）"""
        if model in self.MODEL_OPTIONS:
            self.default_model = model
            self.default_model_var.set(self._key_to_display.get(model, model))

    def set_template_options(self, templates: dict[str, str], default: str = ""):
        """设置模板选项（从 config_manager 获取）

        Args:
            templates: 模板名称 -> 提示词内容的字典
            default: 默认选中的模板名称
        """
        self._template_options = templates.copy()
        self._default_template = default

        # 构建下拉框选项列表（添加"使用全局配置"选项）
        template_names = ["使用全局配置"] + list(templates.keys())

        # 更新所有现有行的模板下拉框
        for file_path, widgets in self._row_widgets.items():
            if "template_combo" in widgets:
                widgets["template_combo"]["values"] = template_names
                # 如果当前有默认模板，设置它
                if default and default in templates:
                    widgets["template_var"].set(default)
                    # 同时更新 item 的 prompt
                    if file_path in self.files:
                        self.files[file_path].prompt = templates[default]
                else:
                    widgets["template_var"].set("使用全局配置")

    def _preview_image(self, file_path: str):
        """预览图片"""
        try:
            from PIL import Image, ImageTk

            # 创建预览窗口
            preview_window = tk.Toplevel(self)
            preview_window.title(f"预览 - {Path(file_path).name}")
            preview_window.geometry("800x600")

            # 加载图片
            img = Image.open(file_path)

            # 缩放以适应窗口
            max_size = (760, 520)
            img.thumbnail(max_size, Image.LANCZOS)

            photo = ImageTk.PhotoImage(img)

            # 显示图片
            label = ttk.Label(preview_window, image=photo)
            label.image = photo  # 保持引用
            label.pack(padx=20, pady=20)

            # 显示信息
            info = f"尺寸: {img.width} x {img.height} | 路径: {file_path}"
            ttk.Label(preview_window, text=info, wraplength=760).pack(pady=10)

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"无法预览图片: {e}")
