# 修图工具 - 项目文档

## 项目简介

一个GUI桌面应用程序，用于自动识别并去除电商图片中的品牌水印、平台标识和营销文字。

## 核心功能

1. **OCR文字检测** - 识别图片中的文字位置
2. **智能过滤** - 根据屏蔽词列表筛选需要去除的文字
3. **图像修复** - 使用AI模型修复被抹除的区域
4. **批量处理** - 支持文件夹批量处理
5. **多模型选择** - 每张图片可单独选择AI模型（v1.6）
6. **提示词模板** - 支持保存和管理常用Prompt模板（v1.7新增）
7. **每图模板** - 每张图片可独立选择提示词模板（v1.8新增）

## 技术架构

### 技术栈
- **GUI**: tkinter (Python内置)
- **OCR/修复API**: 支持多服务商 (Nano Banana, 通义千问, Seedream, Wan等)
- **打包**: PyInstaller (单文件exe)

### 核心模块

```
core/
├── config.py              # 配置管理 (读取providers.yaml)
├── api_adapter.py         # 统一API适配器（多服务商基类）
├── nanobanana_adapter.py  # NanoBanana API适配器
├── gemini_adapter.py      # Google Gemini API适配器
├── scene_detector.py      # 场景自动检测
├── mask_generator.py      # 遮罩生成
└── workflow.py            # 处理工作流（支持多服务商切换）

gui/
├── config_manager.py      # GUI配置持久化（含模板管理）
├── config_panel.py        # 左侧配置面板（含模板选择）
├── template_manager.py    # 模板管理对话框（v1.7新增）
├── file_list.py           # 文件列表组件
├── worker.py              # 后台处理线程
└── main_window.py         # 主窗口
```

## 项目结构

```
E:\image-text-remover\
├── gui_app.py              # GUI入口
├── main.py                 # 命令行入口（保留）
├── build_exe.py            # 打包脚本
├── providers.yaml          # 服务商配置 + Prompt模板
├── requirements.txt        # 依赖
├── core/                   # 核心模块
├── gui/                    # GUI模块
├── config/
│   ├── blocklist.txt      # 屏蔽词列表
│   └── settings.json      # 用户配置（自动创建）
├── input/                  # 输入文件夹
├── output/                 # 输出文件夹
├── dist/                   # 打包输出
│   └── 修图工具.exe       # 可执行文件
└── .venv/                  # Python虚拟环境
```

## 配置说明

### providers.yaml

```yaml
# 默认服务商
default_ocr: nano_banana
default_inpaint: nano_banana

# 服务商配置
providers:
  nano_banana_ocr:
    auth:
      api_key: "你的API Key"
  nano_banana_inpaint:
    auth:
      api_key: "你的API Key"

# Prompt策略
ecommerce:
  prompt_strategy: auto  # auto/universal

  # 通用Prompt
  universal_prompt:
    positive: "..."
    negative: "..."

  # 场景专用Prompt
  inpaint_prompts:
    white_background:
      positive: "..."
      negative: "..."
```

### 屏蔽词列表 (config/blocklist.txt)

```
天猫
TMALL
淘宝
京东
©
®
™
```

### 处理报告 (output/report.json)

每次处理完成后自动生成JSON报告：

```json
{
  "report_info": {
    "generated_at": "2026-03-04T15:08:10",
    "total_images": 5,
    "success_count": 3,
    "failed_count": 2,
    "output_dir": "output"
  },
  "results": [
    {
      "url": "https://example.com/1.jpg",
      "filename": "1",
      "output_path": "output/1_clean.jpg",
      "success": true,
      "message": "处理成功",
      "timestamp": "2026-03-04T15:08:10"
    }
  ]
}
```

## 使用方式

### 开发环境运行
```bash
# 激活虚拟环境
cd e:/image-text-remover
.venv\Scripts\activate

# 运行GUI
python gui_app.py
```

### 打包exe
```bash
python build_exe.py
```

输出: `dist/修图工具.exe`

### 使用 Google Gemini（推荐）

1. 获取 API Key
   - 访问 https://aistudio.google.com/api-keys
   - 创建新的 API Key

2. 配置软件
   - 打开 `dist/修图工具.exe`
   - 左侧选择 "Google Gemini"
   - 填入 API Key

3. 添加图片
   - 点击 "📁 添加图片" 选择本地文件（支持 .jpg/.png/.webp）
   - 或点击 "📂 添加文件夹" 批量添加

4. 编辑 Prompt（重要）
   - Gemini 对敏感词有限制，避免使用 "watermark", "logo" 等词
   - 推荐 Prompt: `Clean up the image by removing text overlays and signatures. Keep the product intact.`
   - 或: `Remove all visible text and annotations from the image while preserving the product.`

5. 开始处理
   - 点击 "开始处理"
   - 处理完成后自动打开输出文件夹
   - 查看 `output/` 目录获取结果

### 使用 NanoBanana

1. 访问 https://www.nanobanana.com 注册获取 API Key
2. 左侧选择 "NanoBanana"
3. 填入 API Key
4. **注意**: NanoBanana 只支持网络图片 URL，不支持本地文件

## 注意事项

### Google Gemini Prompt 限制

Gemini API 有内容安全策略，以下词汇可能触发拒绝：

- ❌ `watermark` - 被认为是侵犯知识产权
- ❌ `logo` - 被认为是侵犯商标权
- ❌ `remove brand` - 被认为是虚假宣传

**建议替代方案**：

| 避免使用 | 推荐使用 |
|---------|---------|
| Remove watermarks | Clean up the image |
| Remove logos | Remove text overlays |
| Remove brand names | Remove annotations |
| Erase copyright | Restore original state |

### 自动打开输出文件夹

处理完成后，如果有至少一张图片成功处理，程序会自动打开输出文件夹。如需禁用此功能，可修改 `gui/main_window.py` 中的 `_on_finished_ui` 方法。

## 服务商对比

| 特性 | Google Gemini | NanoBanana |
|------|---------------|------------|
| **图片输入** | 本地文件 ✅ / URL ✅ | 仅 URL ✅ |
| **处理模式** | 同步（即时返回） | 异步（轮询等待） |
| **模型** | gemini-2.5-flash-image | Gemini 2.5 Flash |
| **API Key** | Google AI Studio | NanoBanana 官网 |
| **内容限制** | 较严格（拒绝水印相关请求） | 较宽松 |
| **稳定性** | 高（Google 官方） | 中（第三方封装） |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## Prompt策略

| 策略 | 说明 |
|------|------|
| **自动检测** | 自动识别图片类型，使用对应prompt |
| **通用模式** | 所有图片使用同一套prompt |
| **指定场景** | 强制使用白底/场景/服装等专用prompt |

## 可用模型（v1.6+）

支持在文件列表中为每张图片单独选择模型：

| 模型名称 | 显示名称 | 特点 | 推荐场景 |
|---------|---------|------|---------|
| `gemini-2.5-flash-image` | Nano Banana | 速度最快，处理效率高 | 批量处理、简单编辑 |
| `gemini-3.1-flash-image-preview` | Nano Banana 2 | 预览版，平衡型 | 一般质量要求 |
| `gemini-3-pro-image-preview` | Nano Banana Pro | 质量最高，复杂推理 | 高质量要求、复杂场景 |

**模型选择方式：**
- 每张图片右侧下拉框单独选择
- 底部工具栏可设置"默认模型"（操作按钮和模型选择分两行布局）
- 处理报告中会记录每张图使用的模型

## 提示词模板（v1.7+ / v1.8+）

支持保存和管理常用提示词模板：

| 模板名称 | 用途 |
|---------|------|
| 通用去水印 | 去除文字、水印、Logo、品牌名 |
| 去除品牌标识 | 专注去除商标、版权符号 |
| 产品图优化 | 清理产品图上的标签和注释 |
| 清空背景文字 | 只清理背景文字，保留主体 |

**使用方法：**
1. 从"模板"下拉框选择预设模板，自动填充到提示词框
2. 编辑提示词后，点击"保存为模板"存为新模板（可覆盖已有模板）
3. 选择模板后，点击"更新当前模板"可直接覆盖原模板内容
4. 点击"删除"可删除当前选中的自定义模板（默认模板不可删除）
5. 点击"管理"打开模板管理器：
   - 左侧选择模板，右侧编辑内容
   - **4个默认模板不可删除**，可以修改内容
   - 重命名默认模板时会**自动复制**为新模板（保留原默认模板）
   - 自定义模板可以删除、重命名
   - 可复制任意模板创建新模板
   - 选中默认模板时，可点击"重置为默认"恢复该模板的初始内容

## 更新记录

### v1.8
- [x] 新增每图独立选择模板功能，每张图片可单独选择提示词模板
- [x] 文件列表每行增加"提示词模板"选择下拉框
- [x] 新增模板同步机制，配置面板模板变化自动同步到处理区域
- [x] 支持"使用全局配置"选项，选择后使用左侧配置面板的提示词
- [x] 支持为每张图片单独设置提示词，实现更灵活的处理策略

### v1.7
- [x] 新增提示词模板管理功能
- [x] 4个内置模板：通用去水印、去除品牌标识、产品图优化、清空背景文字
- [x] 支持保存自定义模板，一键将当前提示词存为模板
- [x] 支持快速更新：选择模板后可直接"更新当前模板"覆盖内容
- [x] 支持快速删除：选择自定义模板后可直接"删除"（默认模板不可删除）
- [x] 模板管理对话框：左右分栏设计，左侧列表右侧编辑
- [x] 支持编辑模板内容、重命名模板、删除模板、复制为新模板
- [x] **4个默认模板不可删除**，可修改内容，重命名时自动复制保留原模板
- [x] 模板选择下拉框，快速切换常用提示词
- [x] 当前选中模板自动保存，下次启动自动恢复
- [x] 支持"重置为默认"功能，一键恢复默认模板的初始内容
- [x] 删除模板后自动同步到处理区域的模板选择框

### v1.6
- [x] 新增多模型选择功能，每张图片可单独选择模型
- [x] 支持三个 Gemini 图像生成模型：2.5 Flash / 3.1 Flash Preview / 3 Pro Preview
- [x] 文件列表组件重写，支持模型选择下拉框
- [x] 新增模型使用统计（report.json 中记录各模型成功率）
- [x] 增加 API 请求超时时间到 300 秒，支持大图片处理
- [x] 优化文件列表 UI，显示状态、文件名、模型选择

### v1.5
- [x] 修复 Gemini API 响应字段解析问题（`inlineData` 驼峰命名）
- [x] 添加自动打开输出文件夹功能（处理完成后自动弹出）
- [x] 添加 API 响应调试日志，便于排查问题
- [x] 更新 Prompt 使用建议（避免敏感词触发安全限制）

### v1.4
- [x] 新增 Google Gemini API 支持（默认使用 Gemini）
- [x] 使用 `gemini-2.5-flash-image` 模型进行图像编辑
- [x] 支持本地文件直接处理（无需上传到图床）
- [x] GUI 添加 "📁 添加图片" 和 "📂 添加文件夹" 按钮
- [x] GUI 添加服务商选择下拉框（NanoBanana / Google Gemini）
- [x] 优化错误处理和调试信息输出
- [x] NanoBanana 增加本地文件检测和友好提示

### v1.3
- [x] 自动生成JSON处理报告（output/report.json）
- [x] 改进API错误处理，显示详细错误信息
- [x] 添加API Key调试信息

### v1.2
- [x] 新增通义千问（Qianwen）API支持，支持OCR和图像修复

### v1.1
- [x] 去掉"处理模式"区块（Prompt策略、场景类型选择）
- [x] 正向prompt默认为空，由用户自定义填写
- [x] 反向prompt保留可编辑，用户输入生效
- [x] 修复文件列表区域按钮显示问题
- [x] 优化布局：prompt区域扩大，输出配置移至底部

### v1.0
- [x] GUI界面开发
- [x] 多服务商支持
- [x] 自动场景检测
- [x] 批量处理
- [x] 配置持久化
- [x] 打包exe
