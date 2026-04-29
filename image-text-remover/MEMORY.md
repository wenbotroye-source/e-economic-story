# 修图工具 - 项目记忆

## 项目概述

一个用于电商图片处理的GUI桌面应用程序，自动识别并去除图片中的品牌水印和文字。

## 已完成的功能

### v1.8 版本（当前）
- [x] 每图独立模板：每张图片可单独选择提示词模板
- [x] 文件列表增加"提示词模板"选择列
- [x] 模板同步机制：配置面板模板变化自动同步到处理区域
- [x] 支持"使用全局配置"选项
- [x] FileListItem 添加 prompt 字段存储每图独立提示词

### v1.7 版本
- [x] 提示词模板管理：支持保存、加载、管理自定义Prompt模板
- [x] 4个默认模板：通用去水印、去除品牌标识、产品图优化、清空背景文字
- [x] **默认模板不可删除**，可以修改内容，重命名时会自动复制为新模板
- [x] 模板快速更新：选择模板后可直接"更新当前模板"
- [x] 模板快速删除：选择自定义模板后可直接"删除"（默认模板不可删除）
- [x] 模板重命名：自定义模板可重命名，默认模板重命名时会复制保留原模板
- [x] 模板复制：支持复制任意模板创建新模板
- [x] 模板管理对话框：左右分栏设计，左侧列表右侧编辑
- [x] 重置默认模板：选中默认模板时可一键恢复初始内容
- [x] 删除同步：删除模板后自动同步到处理区域的模板选择框

### v1.6 版本
- [x] 多模型选择：每张图片可单独选择AI模型
- [x] 支持三个模型：Nano Banana / Nano Banana 2 / Nano Banana Pro
- [x] 模型使用统计：report.json 记录各模型使用情况
- [x] 文件列表重写：Canvas + Frame 布局，带模型选择下拉框
- [x] 默认模型设置：新图片自动使用默认模型
- [x] API超时优化：增加到300秒，支持大图片

### v1.0-v1.5 历史版本
- [x] GUI界面（tkinter）
- [x] 多服务商支持（Google Gemini / NanoBanana）
- [x] 批量图片处理
- [x] 配置持久化（settings.json）
- [x] PyInstaller打包exe
- [x] 本地文件直接处理
- [x] JSON处理报告自动生成

## 技术实现

### 核心流程
```
input/图片.jpg
    ↓
OCR API 检测文字位置
    ↓
本地过滤（匹配blocklist.txt）
    ↓
生成mask图
    ↓
Inpainting API 修复图片
    ↓
output/图片_clean.jpg
```

### 关键文件
| 文件 | 用途 |
|------|------|
| `gui_app.py` | GUI程序入口 |
| `gui/main_window.py` | 主窗口，集成文件列表和配置面板 |
| `gui/file_list.py` | 文件列表组件，带模型选择功能 |
| `gui/worker.py` | 后台处理线程，传递模型参数 |
| `gui/config_panel.py` | 左侧配置面板，含提示词模板选择 |
| `gui/config_manager.py` | 配置管理，保存模型设置和模板 |
| `gui/template_manager.py` | 模板管理对话框（新增） |
| `core/workflow.py` | 处理工作流，支持模型参数传入 |
| `providers.yaml` | API配置 + Prompt模板 |
| `config/blocklist.txt` | 屏蔽词列表 |
| `config/settings.json` | 用户配置（自动保存） |
| `build_exe.py` | 打包脚本 |

## 模型对比

| 模型 | 速度 | 质量 | 稳定性 | 推荐场景 |
|------|------|------|--------|---------|
| Nano Banana (2.5 Flash) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 批量处理、速度优先 |
| Nano Banana 2 (3.1 Preview) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 平衡选择 |
| Nano Banana Pro (3 Pro) | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 质量优先、复杂场景 |

**注意：** Nano Banana 2 为预览版，偶尔可能出现超时，建议网络稳定时使用。

## 使用方式

### 运行程序
```bash
# 开发环境
python gui_app.py

# 打包exe
python build_exe.py
```

### 首次使用
1. 在左侧填写API Key
2. 可选：填写正向Prompt（自定义风格）
3. 添加图片，开始处理

## Prompt配置说明

- **正向Prompt**：用户可自定义填写，留空则使用配置默认值
- **反向Prompt**：用户可自定义填写，留空则使用配置默认值

## 修改记录

### 2025-03-09 (v1.8)
- 新增每图独立选择模板功能
- 修改 file_list.py：FileListItem 添加 prompt 字段，_create_file_row 添加模板选择下拉框
- 修改 worker.py：处理时使用 item.prompt 替代全局 prompt
- 修改 main_window.py：添加 _sync_templates_to_file_list 方法，同步模板到文件列表
- 修改 config_panel.py：添加 on_template_change 回调，模板变化时通知主窗口同步
- 模板选择支持"使用全局配置"选项，使用左侧配置面板的提示词

### 2025-03-09 (v1.7)
- 新增提示词模板管理功能
- 修改 config_manager.py：添加 DEFAULT_TEMPLATES 默认模板、prompt_templates 用户模板存储
- 新增模板管理方法：get_all_templates(), save_template(), delete_template(), update_template()
- 修改 config_panel.py：重写 Prompt 区域，添加模板选择下拉框、保存/更新/删除/管理按钮，**删除原"恢复默认"按钮**
- 新建 template_manager.py：模板管理对话框，左右分栏设计
- 支持功能：编辑模板内容、重命名模板、删除模板、复制为新模板
- 4个内置默认模板：通用去水印、去除品牌标识、产品图优化、清空背景文字
- 默认模板不可删除，可修改内容，重命名时自动复制为新模板
- 配置面板添加"删除"按钮：选择自定义模板后可直接删除，删除后自动同步到文件列表
- 模板管理对话框增加"重置为默认"按钮：选中默认模板时可一键恢复初始内容
- 调整底部工具栏布局：操作按钮和模型选择分两行显示，模型下拉框宽度增加到25

### 2025-03-05 (v1.6)
- 重写文件列表组件：从 Treeview 改为 Canvas + Frame 布局
- 添加 FileListItem 数据类：包含 file_path, filename, status, model 字段
- 实现每图模型选择：每张图片右侧显示模型下拉框
- 添加默认模型配置：底部工具栏可选择默认模型
- 修改 worker.py：支持传递 FileListItem 列表，每张图使用各自的模型
- 修改 workflow.py：支持 model 参数传入
- 修改 config_manager.py：添加 default_model 配置项
- 增加 API 超时到 300 秒，避免大图片处理超时
- 更新报告生成：记录每张图使用的模型和模型统计

### 2025-03-04
- 简化界面：移除"处理模式"选择区块
- 调整Prompt逻辑：正向可自定义，反向可编辑且生效
- 优化布局：修复文件列表按钮显示
- 新增通义千问（Qianwen）API选项，支持OCR和图像修复

## Prompt策略

- **自动检测**：根据图片类型自动选择prompt
- **通用模式**：所有图片使用同一套prompt
- **指定场景**：强制使用白底/场景/服装等专用prompt

## 已适配的服务商

| 服务商 | OCR | 图像修复 | 状态 |
|--------|-----|----------|------|
| Nano Banana | ✓ | ✓ | 可用 |
| 通义千问 | ✓ | ✓ | 可用 |
| Seedream | ✓ | ✓ | 预留 |
| Wan API | ✓ | ✓ | 预留 |
| 百度OCR | ✓ | - | 预留 |
| 阿里云 | ✓ | - | 预留 |

## 待优化项

- [ ] 处理效果预览
- [ ] 断点续传
- [ ] 更多服务商适配

## 项目位置

`E:\image-text-remover`
