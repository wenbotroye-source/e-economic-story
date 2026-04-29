"""
主窗口 - 支持每图选择模型
整合所有组件
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from urllib.parse import urlparse

from .config_manager import GUIConfigManager
from .config_panel import ConfigPanel
from .file_list import FileList, FileListItem
from .worker import ProcessWorker


class MainWindow(tk.Tk):
    """主窗口 - 支持每图选择模型"""

    def __init__(self):
        super().__init__()

        self.title("修图工具 v1.8 - 支持多模型和每图模板")
        self.geometry("1100x750")
        self.minsize(900, 650)

        # 配置管理器
        self.config_manager = GUIConfigManager()

        # 处理线程
        self.worker = None

        self._create_menu()
        self._create_layout()
        self._create_status_bar()

        # 协议处理
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # 加载默认模型和模板配置
        self.file_list.set_default_model(self.config_manager.default_model)
        self._sync_templates_to_file_list()

    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="清空列表", command=self._clear_list)
        file_menu.add_separator()
        file_menu.add_command(label="打开输出目录", command=self._open_output_dir)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_close)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)

    def _create_layout(self):
        """创建主布局"""
        # 主容器
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # 配置主框架的grid权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        # 左侧配置面板（传入模板变化回调）
        self.config_panel = ConfigPanel(main_frame, self.config_manager, on_template_change=self._sync_templates_to_file_list)
        self.config_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # 右侧处理面板
        self._create_process_panel(main_frame)
        self.process_panel.grid(row=0, column=1, sticky="nsew")

        # 底部控制面板
        self._create_control_panel(main_frame)
        self.control_panel.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def _create_process_panel(self, parent):
        """创建右侧处理面板"""
        self.process_panel = ttk.LabelFrame(parent, text="🚀 处理区域", padding=10)

        # 文件列表（新的组件，带模型选择）
        self.file_list = FileList(self.process_panel, on_selection_change=None)
        self.file_list.pack(fill="both", expand=True)

        # 进度条
        progress_frame = ttk.Frame(self.process_panel)
        progress_frame.pack(fill="x", pady=10)

        ttk.Label(progress_frame, text="总进度:").pack(side="left")
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var,
            maximum=100, mode="determinate", length=200
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side="left")

        # 日志区域
        log_frame = ttk.LabelFrame(self.process_panel, text="📋 处理日志", padding=5)
        log_frame.pack(fill="x", pady=5)

        self.log_text = tk.Text(log_frame, height=5, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True)

        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side="right", fill="y")

    def _create_control_panel(self, parent):
        """创建底部控制面板"""
        self.control_panel = ttk.Frame(parent)

        # 输出目录选择
        ttk.Label(self.control_panel, text="输出目录:").pack(side="left")
        self.output_dir = tk.StringVar(value="./output")
        ttk.Entry(self.control_panel, textvariable=self.output_dir, width=40).pack(side="left", padx=5)
        ttk.Button(self.control_panel, text="浏览", command=self._select_output_dir).pack(side="left")

        # 控制按钮
        ttk.Separator(self.control_panel, orient="vertical").pack(side="left", fill="y", padx=10)

        self.start_btn = ttk.Button(
            self.control_panel, text="开始处理",
            command=self._start_processing
        )
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(
            self.control_panel, text="停止",
            command=self._stop_processing,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)

    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self, relief="sunken", padding="2")
        self.status_bar.pack(side="bottom", fill="x")

        self.status_label = ttk.Label(self.status_bar, text="就绪")
        self.status_label.pack(side="left", padx=5)

        ttk.Separator(self.status_bar, orient="vertical").pack(side="left", fill="y", padx=5)

        self.url_count_label = ttk.Label(self.status_bar, text="图片数: 0")
        self.url_count_label.pack(side="left", padx=5)

    def _clear_list(self):
        """清空列表"""
        if messagebox.askyesno("确认", "确定要清空所有图片吗？"):
            self.file_list.clear()
            self._update_url_count()

    def _update_url_count(self):
        """更新图片计数"""
        count = len(self.file_list.get_files())
        self.url_count_label.config(text=f"图片数: {count}")

    def _sync_templates_to_file_list(self):
        """将模板配置同步到文件列表组件"""
        templates = self.config_manager.get_all_templates()
        self.file_list.set_template_options(templates, self.config_manager.selected_template)

    def _select_output_dir(self):
        """选择输出目录"""
        from tkinter import filedialog
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.output_dir.set(dir_path)

    def _open_output_dir(self):
        """打开输出目录"""
        import os
        import subprocess
        import time

        output_path = Path(self.output_dir.get())
        output_path.mkdir(parents=True, exist_ok=True)

        # 尝试多次打开目录，处理文件锁定问题
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if os.name == 'nt':  # Windows
                    # 使用explorer命令打开文件夹
                    # 注意：explorer通常返回1，这不是错误
                    subprocess.run(['explorer', str(output_path)],
                                 shell=True, timeout=5, check=False)
                else:  # macOS/Linux
                    subprocess.run(['open', str(output_path)], timeout=5, check=True)

                # 成功打开，退出重试循环
                break
            except subprocess.TimeoutExpired:
                if attempt < max_retries - 1:
                    self._log(f"[警告] 打开目录超时，重试中... ({attempt + 1}/{max_retries})")
                    time.sleep(1)
                else:
                    self._log("[错误] 打开目录超时，已放弃")
            except subprocess.CalledProcessError as e:
                if attempt < max_retries - 1:
                    self._log(f"[警告] 打开目录失败，重试中... ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(1)
                else:
                    self._log(f"[错误] 打开目录失败: {e}")
            except Exception as e:
                if attempt < max_retries - 1:
                    self._log(f"[警告] 打开目录异常，重试中... ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(1)
                else:
                    self._log(f"[错误] 打开目录异常: {e}")
                    # 最后尝试：只显示目录路径
                    self._log(f"[信息] 输出目录路径: {output_path}")

    def _start_processing(self):
        """开始处理"""
        # 获取待处理文件（不含参考图）
        waiting_items = self.file_list.get_waiting_files()

        # 获取参考图
        reference_items = self.file_list.get_reference_files()

        self._log(f"调试: 待处理文件数量: {len(waiting_items)}, 参考图数量: {len(reference_items)}")

        if not waiting_items:
            if reference_items:
                messagebox.showwarning("警告", "所有图片都标记为参考图，请至少保留一张待处理图片！")
            else:
                messagebox.showwarning("警告", "没有待处理的文件！")
            return

        # 保存配置
        config = self.config_panel.get_config_dict()

        # 检查API Key
        if not config.get('api_key'):
            provider_name = "Google Gemini" if config.get('provider') == 'gemini' else "NanoBanana"
            messagebox.showerror("错误", f"请先填写 {provider_name} API Key！")
            return

        # 更新状态为等待
        for item in waiting_items:
            self.file_list.update_status(item.file_path, "处理中", "初始化...")

        # 创建处理线程
        self.worker = ProcessWorker(
            file_items=waiting_items,
            output_dir=self.output_dir.get(),
            config=config,
            progress_callback=self._on_progress,
            finished_callback=self._on_finished,
            reference_items=reference_items if reference_items else None
        )

        # 更新UI状态
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="处理中...")
        self.progress_var.set(0)

        # 启动线程
        self.worker.start()

    def _stop_processing(self):
        """停止处理"""
        if self.worker and self.worker.is_alive():
            self.worker.stop()
            self._log("正在停止处理...")

    def _on_progress(self, file_path: str, status: str, progress: int, message: str):
        """进度回调"""
        # 在主线程更新UI
        self.after(0, lambda: self._update_progress(file_path, status, progress, message))

    def _update_progress(self, file_path: str, status: str, progress: int, message: str):
        """更新进度（主线程）"""
        # 更新列表状态
        self.file_list.update_status(file_path, status, message)

        # 计算总进度（不含参考图）
        all_items = self.file_list.get_files()
        total_files = sum(1 for item in all_items if not item.is_reference)
        if total_files > 0:
            processed = sum(1 for item in all_items
                          if not item.is_reference and item.status in ("完成", "失败"))
            overall_progress = int((processed / total_files) * 100)
        else:
            overall_progress = progress

        # 更新进度条
        self.progress_var.set(overall_progress)
        self.progress_label.config(text=f"{overall_progress}%")

        # 更新状态栏
        filename = Path(file_path).name
        self.status_label.config(text=f"{status}: {filename}")

        # 添加日志
        self._log(f"[{status}] {filename}: {message}")

    def _on_finished(self):
        """处理完成回调"""
        self.after(0, self._on_finished_ui)

    def _on_finished_ui(self):
        """处理完成UI更新（主线程）"""
        import time

        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="处理完成")
        self.progress_var.set(100)
        self.progress_label.config(text="100%")

        self._log("=" * 50)
        self._log("所有文件处理完成！")

        # 统计结果（不含参考图）
        items = self.file_list.get_files()
        done_count = sum(1 for item in items if not item.is_reference and item.status == "完成")
        error_count = sum(1 for item in items if not item.is_reference and item.status == "失败")

        # 保存默认模型配置
        self.config_manager.default_model = self.file_list.default_model
        self.config_manager.save()

        # 等待一小段时间确保所有文件操作完成
        time.sleep(1)

        # 自动打开输出文件夹（如果有成功处理的图片）
        if done_count > 0:
            try:
                self._open_output_dir()
            except Exception as e:
                self._log(f"[警告] 打开输出目录失败: {e}")

        messagebox.showinfo(
            "完成",
            f"处理完成！\n\n成功: {done_count}\n失败: {error_count}\n\n输出文件夹已打开。"
        )

    def _log(self, message: str):
        """添加日志"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _show_help(self):
        """显示帮助"""
        help_text = """
使用说明：

1. 配置API
   - 在左侧填写 Google Gemini API Key
   - 可选：修改编辑提示词（Prompt）

2. 添加图片
   - 点击"添加图片"选择本地文件
   - 或点击"添加文件夹"批量导入
   - 支持 JPG、PNG、WebP 格式

3. 选择模型（重要！）
   - 每张图片右侧可选择使用的模型：
     * Nano Banana (2.5 Flash) - 速度快，适合简单处理
     * Nano Banana 2 (3.1 Flash Preview) - 预览版，平衡型
     * Nano Banana Pro (3 Pro Preview) - 高质量，复杂任务
   - 也可在底部设置"默认模型"

4. 选择提示词模板（v1.8+）
   - 每张图片可选择独立的提示词模板
   - 选择"使用全局配置"则使用左侧配置的提示词
   - 也可选择预设模板（通用去水印、产品图优化等）

5. 开始处理
   - 选择输出目录
   - 点击"开始处理"按钮
   - 等待处理完成

5. 查看结果
   - 处理完成后自动打开输出目录
   - 查看 report.json 了解详细处理结果

提示：
- 不同模型的效果和速度有差异，可以对比测试
- 批量处理时建议先用小图测试效果
        """
        messagebox.showinfo("使用说明", help_text)

    def _show_about(self):
        """显示关于"""
        messagebox.showinfo(
            "关于",
            "修图工具 v1.8\n\n"
            "支持多模型选择和每图独立提示词模板\n\n"
            "功能特性：\n"
            "- 每图可选择不同模型和提示词模板\n"
            "- 4个内置提示词模板（可自定义）\n"
            "- 批量处理，自动打开输出目录\n\n"
            "可用模型：\n"
            "- Nano Banana (Gemini 2.5 Flash)\n"
            "- Nano Banana 2 (Gemini 3.1 Flash Preview)\n"
            "- Nano Banana Pro (Gemini 3 Pro Preview)\n\n"
            "支持格式：JPG、PNG、WebP"
        )

    def _on_close(self):
        """关闭窗口"""
        if self.worker and self.worker.is_alive():
            if messagebox.askyesno("确认", "正在处理中，确定要退出吗？"):
                self.worker.stop()
                self.worker.join(timeout=2)
            else:
                return

        # 保存配置
        self.config_panel.save_config()

        self.destroy()


def main():
    """主函数"""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
