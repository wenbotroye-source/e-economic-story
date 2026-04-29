"""
模板管理对话框 - 管理提示词模板
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


class TemplateManagerDialog(tk.Toplevel):
    """模板管理对话框"""

    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.config = config_manager

        self.title("管理提示词模板")
        self.geometry("550x450")
        self.minsize(500, 350)

        # 模态对话框
        self.transient(parent)
        self.grab_set()

        self.selected_template = None  # 当前选中的模板

        self._create_ui()
        self._refresh_list()

        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_ui(self):
        """创建界面"""
        # 主容器
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # 说明标签
        ttk.Label(main_frame,
                 text="管理提示词模板（4个默认模板不可删除，重命名时会自动复制）",
                 font=("Arial", 9), foreground="gray").pack(anchor="w", pady=(0, 5))

        # 左右分栏
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=5)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        # 左侧：模板列表
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        ttk.Label(left_frame, text="模板列表", font=("Arial", 9, "bold")).pack(anchor="w")

        # 列表框和滚动条
        list_container = ttk.Frame(left_frame)
        list_container.pack(fill="both", expand=True, pady=2)

        self.template_listbox = tk.Listbox(
            list_container,
            selectmode="single",
            height=10
        )
        scrollbar = ttk.Scrollbar(list_container, orient="vertical",
                                  command=self.template_listbox.yview)
        self.template_listbox.configure(yscrollcommand=scrollbar.set)

        self.template_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 绑定选择事件
        self.template_listbox.bind("<<ListboxSelect>>", self._on_list_select)
        self.template_listbox.bind("<Double-Button-1>", self._on_double_click)

        # 列表按钮
        list_btn_frame = ttk.Frame(left_frame)
        list_btn_frame.pack(fill="x", pady=5)

        self.rename_btn = ttk.Button(list_btn_frame, text="重命名",
                                     command=self._rename_template, state="disabled")
        self.rename_btn.pack(side="left", padx=2)

        self.delete_btn = ttk.Button(list_btn_frame, text="删除",
                                     command=self._delete_template, state="disabled")
        self.delete_btn.pack(side="left", padx=2)

        # 右侧：编辑区域
        right_frame = ttk.LabelFrame(content_frame, text="模板编辑", padding=5)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # 模板名称（只读显示）
        name_frame = ttk.Frame(right_frame)
        name_frame.pack(fill="x", pady=2)

        ttk.Label(name_frame, text="名称:").pack(side="left")
        self.name_label = ttk.Label(name_frame, text="（未选择）", font=("Arial", 9, "bold"))
        self.name_label.pack(side="left", padx=5)

        self.type_label = ttk.Label(name_frame, text="", foreground="gray", font=("Arial", 8))
        self.type_label.pack(side="right")

        # 模板内容编辑框
        ttk.Label(right_frame, text="提示词内容:").pack(anchor="w", pady=(10, 2))

        content_frame_inner = ttk.Frame(right_frame)
        content_frame_inner.pack(fill="both", expand=True)

        self.content_text = tk.Text(content_frame_inner, wrap="word", height=10,
                                    font=("Arial", 9))
        self.content_text.pack(side="left", fill="both", expand=True)

        content_scrollbar = ttk.Scrollbar(content_frame_inner, orient="vertical",
                                          command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scrollbar.set)
        content_scrollbar.pack(side="right", fill="y")

        # 编辑按钮
        edit_btn_frame = ttk.Frame(right_frame)
        edit_btn_frame.pack(fill="x", pady=5)

        self.save_btn = ttk.Button(edit_btn_frame, text="保存修改",
                                   command=self._save_edit, state="disabled")
        self.save_btn.pack(side="left", padx=2)

        self.reset_btn = ttk.Button(edit_btn_frame, text="重置为默认",
                                    command=self._reset_to_default, state="disabled")
        self.reset_btn.pack(side="left", padx=2)

        ttk.Button(edit_btn_frame, text="复制为新模板",
                   command=self._copy_as_new).pack(side="left", padx=2)

        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(bottom_frame,
                 text="提示：双击编辑，默认模板可重置、重命名时复制，自定义模板可删除",
                 font=("Arial", 8), foreground="gray").pack(side="left")

        ttk.Button(bottom_frame, text="关闭",
                   command=self._on_close).pack(side="right")

    def _refresh_list(self):
        """刷新模板列表"""
        self.template_listbox.delete(0, "end")

        # 添加所有模板
        for name in self.config.get_template_names():
            self.template_listbox.insert("end", name)

        # 清空编辑区
        self._clear_edit_area()

    def _clear_edit_area(self):
        """清空编辑区域"""
        self.selected_template = None
        self.name_label.config(text="（未选择）")
        self.type_label.config(text="")
        self.content_text.delete("1.0", "end")
        self.content_text.config(state="disabled")
        self.rename_btn.config(state="disabled")
        self.delete_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.reset_btn.config(state="disabled")

    def _on_list_select(self, event=None):
        """列表选择事件"""
        selection = self.template_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        name = self.template_listbox.get(idx)
        self.selected_template = name

        # 获取内容并显示
        content = self.config.get_template_content(name)

        self.name_label.config(text=name)
        self.type_label.config(text="")

        # 所有模板都可以编辑
        self.content_text.config(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", content)
        self.rename_btn.config(state="normal")
        self.delete_btn.config(state="normal")
        self.save_btn.config(state="normal")

        # 默认模板显示重置按钮
        if self.config.is_default_template(name):
            self.reset_btn.config(state="normal")
        else:
            self.reset_btn.config(state="disabled")

    def _on_double_click(self, event=None):
        """双击编辑"""
        if self.selected_template:
            self.content_text.focus()

    def _save_edit(self):
        """保存当前编辑"""
        if not self.selected_template:
            return

        new_content = self.content_text.get("1.0", "end-1c").strip()
        if not new_content:
            messagebox.showwarning("警告", "提示词内容不能为空")
            return

        # 保存（只更新内容，不改名）
        if self.config.save_template(self.selected_template, new_content):
            messagebox.showinfo("成功", f"模板 '{self.selected_template}' 已更新")
        else:
            messagebox.showerror("错误", "保存失败")

    def _reset_to_default(self):
        """将当前默认模板重置为初始内容"""
        if not self.selected_template:
            return

        # 检查是否为默认模板
        if not self.config.is_default_template(self.selected_template):
            messagebox.showwarning("警告", "只有默认模板可以重置")
            return

        # 确认重置
        if messagebox.askyesno(
            "确认重置",
            f"确定要将模板 '{self.selected_template}' 重置为默认内容吗？\n"
            "这将丢失你对该模板的修改。"
        ):
            # 获取默认内容
            default_content = self.config.DEFAULT_TEMPLATES.get(self.selected_template)
            if default_content:
                # 更新模板内容
                self.config.prompt_templates[self.selected_template] = default_content
                self.config.save()

                # 更新编辑框显示
                self.content_text.delete("1.0", "end")
                self.content_text.insert("1.0", default_content)

                messagebox.showinfo("成功", f"模板 '{self.selected_template}' 已重置为默认内容")
            else:
                messagebox.showerror("错误", "找不到默认模板内容")

    def _rename_template(self):
        """重命名模板"""
        if not self.selected_template:
            return

        # 弹出输入框
        new_name = simpledialog.askstring(
            "重命名模板",
            f"将 '{self.selected_template}' 重命名为：",
            parent=self,
            initialvalue=self.selected_template
        )

        if not new_name:
            return

        new_name = new_name.strip()

        if new_name == self.selected_template:
            return

        # 检查是否已存在
        if new_name in self.config.get_template_names():
            messagebox.showerror("错误", f"模板 '{new_name}' 已存在")
            return

        # 获取当前内容
        content = self.content_text.get("1.0", "end-1c")

        # 判断是否为默认模板
        is_default = self.config.is_default_template(self.selected_template)

        if is_default:
            # 默认模板重命名 = 复制为新模板（保留原默认模板）
            if self.config.save_template(new_name, content):
                self.selected_template = new_name
                self._refresh_list()
                # 重新选中新模板
                for i in range(self.template_listbox.size()):
                    if self.template_listbox.get(i) == new_name:
                        self.template_listbox.selection_clear(0, "end")
                        self.template_listbox.selection_set(i)
                        self.template_listbox.see(i)
                        self._on_list_select()
                        break
                messagebox.showinfo("成功", f"已创建新模板 '{new_name}'\n（原默认模板已保留）")
            else:
                messagebox.showerror("错误", "创建新模板失败")
        else:
            # 普通模板重命名 = 移动
            if self.config.update_template(self.selected_template, new_name, content):
                self.selected_template = new_name
                self._refresh_list()
                # 重新选中
                for i in range(self.template_listbox.size()):
                    if self.template_listbox.get(i) == new_name:
                        self.template_listbox.selection_clear(0, "end")
                        self.template_listbox.selection_set(i)
                        self.template_listbox.see(i)
                        self._on_list_select()
                        break
                messagebox.showinfo("成功", f"模板已重命名为 '{new_name}'")
            else:
                messagebox.showerror("错误", "重命名失败")

    def _delete_template(self):
        """删除模板"""
        if not self.selected_template:
            return

        # 检查是否为默认模板（默认模板不可删除）
        if self.config.is_default_template(self.selected_template):
            messagebox.showwarning(
                "无法删除",
                f"'{self.selected_template}' 是默认模板，不能删除。\n"
                "你可以修改内容或重命名，但无法删除。"
            )
            return

        if messagebox.askyesno("确认删除", f"确定要删除模板 '{self.selected_template}' 吗？"):
            if self.config.delete_template(self.selected_template):
                self._refresh_list()
                messagebox.showinfo("成功", f"模板 '{self.selected_template}' 已删除")
            else:
                messagebox.showerror("错误", "删除失败")

    def _copy_as_new(self):
        """复制当前内容为新建模板"""
        content = self.content_text.get("1.0", "end-1c").strip()
        if not content:
            messagebox.showwarning("警告", "提示词内容为空")
            return

        # 弹出输入框
        default_name = f"{self.selected_template}_副本" if self.selected_template else "新模板"
        new_name = simpledialog.askstring(
            "复制为新模板",
            "请输入新模板名称：",
            parent=self,
            initialvalue=default_name
        )

        if not new_name:
            return

        new_name = new_name.strip()

        if new_name in self.config.get_template_names():
            messagebox.showerror("错误", f"模板 '{new_name}' 已存在")
            return

        if self.config.save_template(new_name, content):
            self._refresh_list()
            # 选中新模板
            for i in range(self.template_listbox.size()):
                if self.template_listbox.get(i) == new_name:
                    self.template_listbox.selection_clear(0, "end")
                    self.template_listbox.selection_set(i)
                    self.template_listbox.see(i)
                    self._on_list_select()
                    break
            messagebox.showinfo("成功", f"已创建新模板 '{new_name}'")
        else:
            messagebox.showerror("错误", "创建失败")

    def _on_close(self):
        """关闭对话框"""
        self.destroy()
