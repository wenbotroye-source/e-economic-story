# 修图工具

自动识别并去除电商图片中的品牌水印、平台标识和营销文字。

## 功能特性

- **GUI界面** - 可视化操作，无需命令行
- **批量处理** - 支持文件夹批量导入
- **多服务商支持** - 支持 Google Gemini / NanoBanana
- **本地文件支持** - 直接处理本地图片，无需上传图床
- **配置持久化** - API Key 和设置自动保存
- **JSON 报告** - 每次处理生成详细报告
- **多模型选择** (v1.6+) - 每张图片可单独选择 AI 模型
- **提示词模板** (v1.7+) - 支持保存和管理常用 Prompt 模板
- **每图模板** (v1.8+) - 每张图片可独立选择提示词模板
- **跨平台支持** (v1.9+) - 支持 Windows / macOS / Linux

## 跨平台支持

本工具支持以下操作系统：

| 操作系统 | 状态 | 说明 |
|---------|------|------|
| Windows | ✅ 支持 | 提供 .exe 安装包 |
| macOS | ✅ 支持 | 提供 .app bundle 或 shell 脚本 |
| Linux | ✅ 支持 | 提供可执行文件或 shell 脚本 |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/image-text-remover.git
cd image-text-remover
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

> **注意**：如果 PowerShell 报错执行策略问题，使用 CMD 或运行：
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. 安装依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 配置 API Key

复制示例配置文件并填入你的 API Key：

```bash
cp config/settings.example.json config/settings.json
```

编辑 `config/settings.json`：

```json
{
  "provider": "gemini",
  "api_key": "your-gemini-api-key-here",
  "model": "gemini-2.5-flash-image"
}
```

**获取 API Key：**
- **Google Gemini（推荐）**：https://aistudio.google.com/api-keys
- **NanoBanana**：https://www.nanobanana.com

> ⚠️ **重要**：`config/settings.json` 包含敏感信息，**不要提交到 Git**（已添加到 .gitignore）

### 5. 运行程序

```bash
# Windows
python gui_app.py

# macOS/Linux
python3 gui_app.py

# 或使用启动脚本
# Windows: 双击 启动工具.bat
# macOS/Linux: ./启动工具.sh
```

## 打包成可执行文件

### Windows

```bash
python build_exe.py
```

输出：`dist/修图工具.exe`

### macOS

```bash
python3 build_exe.py
```

输出：`dist/ImageTextRemover.app` 或 `dist/ImageTextRemover`

### Linux

```bash
python3 build_exe.py
```

输出：`dist/image-text-remover`

## 使用说明

### 添加图片

1. **添加本地图片**：点击 "📁 添加图片" 选择 .jpg/.png/.webp 文件
2. **添加文件夹**：点击 "📂 添加文件夹" 批量导入
3. **支持格式**：jpg、png、webp

### 选择服务商

| 服务商 | 特点 | 推荐度 |
|--------|------|--------|
| **Google Gemini** | 支持本地文件，响应快，稳定性高 | ⭐⭐⭐⭐⭐ |
| **NanoBanana** | 仅支持 URL，内容限制较宽松 | ⭐⭐⭐ |

### 模型选择 (v1.6+)

支持在文件列表中为每张图片单独选择模型：

| 模型名称 | 显示名称 | 特点 | 推荐场景 |
|---------|---------|------|---------|
| `gemini-2.5-flash-image` | Nano Banana | 速度最快，处理效率高 | 批量处理、简单编辑 |
| `gemini-3.1-flash-image-preview` | Nano Banana 2 | 预览版，平衡型 | 一般质量要求 |
| `gemini-3-pro-image-preview` | Nano Banana Pro | 质量最高，复杂推理 | 高质量要求、复杂场景 |

**使用方法：**
- 每张图片右侧下拉框单独选择模型
- 底部工具栏可设置"默认模型"（新添加图片自动使用该模型）
- 处理报告中会记录每张图使用的模型

### 提示词模板 (v1.7+)

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
4. 选择自定义模板后，点击"删除"可直接删除该模板（默认模板不可删除）
5. 点击"管理"打开模板管理器：
   - 左侧选择模板，右侧编辑内容
   - 4个默认模板不可删除，可以修改内容
   - 重命名默认模板时会自动复制为新模板（保留原默认模板）
   - 自定义模板可以删除、重命名
   - 可复制任意模板创建新模板
   - 选中默认模板时，可点击"重置为默认"恢复该模板的初始内容

### Prompt 建议

Google Gemini 有内容安全限制，**避免使用以下词汇**：

| ❌ 避免使用 | ✅ 推荐使用 |
|------------|------------|
| Remove watermarks | Clean up the image |
| Remove logos | Remove text overlays |
| Remove brand names | Remove annotations |
| Erase copyright | Restore original state |

**推荐 Prompt：**
```
Clean up the image by removing text overlays and signatures. Keep the product intact.
```

## 目录结构

```
image-text-remover/
├── input/              # 放置待处理的图片（不会提交到 Git）
├── output/             # 输出处理后的图片 + JSON 报告（不会提交到 Git）
├── config/
│   ├── blocklist.txt   # 屏蔽词列表
│   ├── settings.json   # 用户配置（自动创建，不会提交到 Git）
│   └── settings.example.json  # 配置模板
├── providers.yaml      # 服务商配置 + Prompt 模板
├── gui_app.py          # GUI 程序入口
├── build_exe.py        # 跨平台打包脚本
├── requirements.txt    # Python 依赖
├── core/               # 核心代码
├── gui/                # GUI 模块
├── dist/               # 打包输出（不会提交到 Git）
├── 启动工具.bat         # Windows 启动脚本
└── 启动工具.sh          # macOS/Linux 启动脚本
```

## 打包成可执行文件

### Windows

```bash
python build_exe.py
```

输出：`dist/修图工具.exe`

可将此 exe 文件直接分享给团队成员使用，无需安装 Python。

### macOS

```bash
python3 build_exe.py
```

输出：`dist/ImageTextRemover.app`

macOS 用户可以：
1. 双击 `ImageTextRemover.app` 运行
2. 或在终端运行：`./dist/ImageTextRemover`

### Linux

```bash
python3 build_exe.py
```

输出：`dist/image-text-remover`

Linux 用户在终端运行：`./dist/image-text-remover`

## 输出报告

每次处理完成后，自动生成 `output/report.json`：

```json
{
  "report_info": {
    "generated_at": "2026-03-04T15:08:10",
    "total_images": 5,
    "success_count": 3,
    "failed_count": 2
  },
  "results": [
    {
      "filename": "1.jpg",
      "output_path": "output/1_clean.jpg",
      "success": true,
      "message": "处理成功"
    }
  ]
}
```

## 屏蔽词配置

编辑 `config/blocklist.txt` 添加需要检测的文本：

```
天猫
TMALL
淘宝
京东
©
®
™
```

## 服务商对比

| 特性 | Google Gemini | NanoBanana |
|------|---------------|------------|
| **图片输入** | 本地文件 ✅ / URL ✅ | 仅 URL ✅ |
| **处理模式** | 同步（即时返回） | 异步（轮询等待） |
| **模型** | gemini-2.5-flash-image | Gemini 2.5 Flash |
| **API Key** | Google AI Studio | NanoBanana 官网 |
| **内容限制** | 较严格 | 较宽松 |
| **稳定性** | 高 | 中 |

## 注意事项

1. **API 费用** - 使用 Google Gemini/NanoBanana 可能产生费用，请注意用量
2. **隐私安全** - 图片会上传到 API 服务商服务器处理
3. **敏感信息** - 不要将包含 API Key 的 `config/settings.json` 提交到 Git
4. **输出目录** - `input/` 和 `output/` 目录不会同步到 Git，请自行备份重要图片

## 问题排查

### PowerShell 执行策略错误
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 虚拟环境激活失败（CMD 方式）
```cmd
.venv\Scripts\activate.bat
```

### macOS 无法打开应用
如果提示"无法验证开发者"，请在终端运行：
```bash
xattr -cr dist/ImageTextRemover.app
```

### Linux 权限问题
```bash
chmod +x dist/image-text-remover
```

### 缺少依赖
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 开发团队

- 使用 `git pull` 获取最新代码
- 修改代码前创建新分支：`git checkout -b feature/xxx`
- 提交前确认没有包含敏感信息：`git status`

## 更新日志

### v1.9
- 新增跨平台支持：Windows / macOS / Linux
- 更新打包脚本，自动识别操作系统
- 添加 macOS/Linux 启动脚本 `启动工具.sh`
- 优化 README 文档，添加跨平台说明

### v1.8
- 新增每图独立选择模板功能，每张图片可单独选择提示词模板
- 文件列表每行增加"提示词模板"选择下拉框
- 支持"使用全局配置"选项，选择后使用左侧配置面板的提示词
- 删除模板后自动同步到处理区域的模板选择框

### v1.7
- 新增提示词模板管理功能
- 4个内置模板：通用去水印、去除品牌标识、产品图优化、清空背景文字
- 支持保存自定义模板，一键将当前提示词存为模板
- 支持快速更新：选择模板后可直接"更新当前模板"覆盖内容
- 支持快速删除：选择自定义模板后可直接"删除"（默认模板不可删除）
- 模板管理对话框：左右分栏设计，左侧列表右侧编辑
- 支持编辑模板内容、重命名模板、删除模板、复制为新模板
- 4个默认模板不可删除，可修改内容，重命名时自动复制保留原模板
- 支持"重置为默认"功能，一键恢复默认模板的初始内容

### v1.6
- 新增多模型选择功能，每张图片可单独选择模型
- 支持三个 Gemini 图像生成模型：2.5 Flash / 3.1 Flash Preview / 3 Pro Preview
- 文件列表组件重写，支持模型选择下拉框
- 新增模型使用统计（report.json 中记录各模型成功率）
- 增加 API 请求超时时间到 300 秒，支持大图片处理

### v1.5
- 新增 Google Gemini API 支持（推荐）
- 支持本地文件直接处理
- 添加 JSON 报告生成功能
- 自动打开输出文件夹

### v1.0-v1.4
- GUI 界面开发
- 多服务商支持
- 批量处理功能
- 打包 exe 支持
