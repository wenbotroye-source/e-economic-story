# 电商图片去水印工具 — 开发与测试全流程

---

## Slide 1 — 封面

**电商图片去水印工具**
基于 AI 的批量图片文字智能清除方案

从 v1.0 到 v1.9：一次完整的桌面应用开发实践

---

## Slide 2 — 背景与痛点

**我们要解决什么问题？**

- 电商卖家跨平台铺货时，图片上带有 **天猫、淘宝、京东** 等平台水印
- 手动修图效率低，一张图几分钟，批量处理上百张图耗时巨大
- 传统 OCR + 修复方案准确率不够，容易残留或误删产品信息

**目标：一键批量处理，自动识别 → 过滤 → 修复，输出干净产品图**

---

## Slide 3 — 技术架构总览

```
┌─────────────────────────────────────────────┐
│                  GUI (tkinter)               │
│  ┌──────────┐  ┌──────────────────────────┐  │
│  │ 配置面板  │  │ 文件列表 + 处理日志       │  │
│  │ 服务商/Key│  │ 每图选模型/模板/参考图    │  │
│  │ Prompt   │  │ 进度条 / 状态             │  │
│  └──────────┘  └──────────────────────────┘  │
├─────────────────────────────────────────────┤
│              Workflow (工作流)                │
│  统一调度 → 适配器分发 → 结果保存 → 报告生成  │
├─────────────────────────────────────────────┤
│           API Adapters (适配器层)             │
│  Gemini │ NanoBanana │ LinkAPI │ BananaPro   │
├─────────────────────────────────────────────┤
│           Config (配置层)                     │
│  providers.yaml │ settings.json │ 模板管理    │
└─────────────────────────────────────────────┘
```

**核心技术栈：** Python 3 + tkinter + Pillow + requests + PyYAML
**打包方案：** PyInstaller → 单文件 exe / app

---

## Slide 4 — 版本迭代时间线

| 版本 | 日期 | 核心内容 |
|------|------|---------|
| **v1.0** | 3月初 | GUI 框架 + NanoBanana 服务商 + 批量处理 + 打包 exe |
| **v1.1** | 3月初 | UI 精简：去掉处理模式区块，布局优化 |
| **v1.2** | 3月初 | 新增通义千问 OCR 支持 |
| **v1.3** | 3月初 | JSON 处理报告自动生成 + 错误信息改进 |
| **v1.4** | 3月初 | **Gemini API 接入**（推荐方案），支持本地文件直接处理 |
| **v1.5** | 3月初 | 修复 Gemini 响应解析 + 自动打开输出文件夹 |
| **v1.6** | 3月5日 | **每图独立选模型**，3 个 Gemini 模型，模型统计 |
| **v1.7** | 3月9日 | **提示词模板管理**：4 个默认模板 + 自定义 + 重命名/复制/重置 |
| **v1.8** | 3月9日 | **每图独立选模板**，模板同步机制 |
| **v1.9** | 4月 | 新增 BananaPro 中转站服务商 + 跨平台支持 |

---

## Slide 5 — v1.0~v1.5：从零到可用

**v1.0 基础搭建**
- tkinter 搭建 GUI 框架：配置面板 + 文件列表 + 处理日志
- NanoBanana API 对接：提交任务 → 轮询等待 → 下载结果
- 批量处理流程：文件夹扫描 → 逐张处理 → 输出命名

**v1.4 关键转折：接入 Google Gemini**
- NanoBanana 只支持 URL，Gemini 支持**本地文件直接处理**
- 同步处理模式，不需要轮询，响应更快
- 成为推荐方案，奠定后续迭代基础

**v1.5 稳定性修复**
- 发现 Gemini 返回的字段名是驼峰 `inlineData`（不是下划线 `inline_data`）
- 增加调试日志，快速定位 API 响应解析问题

---

## Slide 6 — v1.6：每图独立选模型

**需求来源：** 不同图片复杂度不同，简单图用快模型，复杂图用高质量模型

**实现方案：**
```
FileListItem
├── file_path: str
├── model: str        ← 每张图绑定一个模型
├── prompt: str       ← 预留（v1.8 启用）
└── status: str
```

**GUI 变化：**
- 文件列表每行增加「模型」下拉框
- 底部工具栏增加「默认模型」选择
- 处理线程按每张图的 model 创建 Workflow

**三个可用模型：**

| 模型 | 特点 | 场景 |
|------|------|------|
| Nano Banana (2.5 Flash) | 最快 | 批量处理、简单编辑 |
| Nano Banana 2 (3.1 Flash Preview) | 平衡 | 一般质量要求 |
| Nano Banana Pro (3 Pro Preview) | 最高质量 | 复杂场景、高质量要求 |

---

## Slide 7 — v1.7：提示词模板系统

**问题：** 每次都要手动输入英文 Prompt，重复劳动

**方案：** 模板管理系统
- 4 个内置默认模板（不可删除，可修改）
- 支持保存/更新/删除/复制/重命名
- 模板管理器：左右分栏，左侧列表右侧编辑

**默认模板设计思路：**
- 「通用去水印」— 移除文字、水印、Logo、品牌名
- 「去除品牌标识」— 专注去除商标、版权符号
- 「产品图优化」— 清理产品图上的标签和注释
- 「清空背景文字」— 只清理背景文字，保留主体

**技术细节：**
- 默认模板重命名时自动复制（保留原模板）
- 模板数据持久化到 `config/settings.json`
- 删除模板后自动同步到处理区域下拉框

---

## Slide 8 — v1.8：每图独立选模板

**需求：** 一批图里有的需要去水印，有的需要清背景，不能用同一个 prompt

**实现：**
- 文件列表每行增加「提示词模板」下拉框
- 选项包括「使用全局配置」+ 所有已保存模板
- 选择模板后自动填入该图的独立 prompt
- 配置面板模板变化时，自动同步到所有行的下拉框

**数据流：**
```
ConfigPanel (模板保存/修改)
    ↓ on_template_change callback
MainWindow._sync_templates_to_file_list()
    ↓ 
FileList.set_template_options()
    ↓ 更新每行 Combobox
每图独立 prompt → Worker 读取 item.prompt
```

---

## Slide 9 — v1.9：新服务商接入实践（BananaPro）

**背景：** 接入新的中转站 API `bananapro.aigenmedia.art`

**遇到的问题与解决：**

| 问题 | 现象 | 解决 |
|------|------|------|
| 认证方式错误 | 401: 缺少 Authorization 头 | `x-goog-api-key` → `Authorization: Bearer` |
| 响应格式不同 | 1K 分辨率返回 fileData(URL) 不是 inlineData(base64) | 同时支持两种解析 |
| 522 超时 | Cloudflare CDN 不稳定 | 300 秒超时 + 重试机制 |

**调试过程：**
1. 用 curl 测试 API 连通性 → 确认 endpoint 正确
2. Python 直接调用 → 发现 401 是认证头的问题
3. 换 Bearer token → 200 成功
4. 带图片请求 → 发现返回 fileData → 适配器增加 URL 下载逻辑

**经验：** 即使文档写了 `x-goog-api-key`，实际 API 可能只认 `Authorization: Bearer`，**一定要实测验证**

---

## Slide 10 — 模块设计亮点

**1. 适配器模式 — 一行代码加新服务商**

```python
# workflow.py
if self.provider == "gemini":
    self.adapter = GeminiAdapter(api_key, model)
elif self.provider == "linkapi":
    self.adapter = LinkAPIAdapter(api_key, model)
elif self.provider == "bananapro":
    self.adapter = BananaProAdapter(api_key, model)
```

新增服务商只需：写一个适配器 + workflow 加一个分支 + GUI 加一个选项

**2. 三配置体系**
- `providers.yaml` — 服务商 API 配置（开发者维护）
- `config/settings.json` — 用户个性化配置（自动持久化）
- `config/blocklist.txt` — 屏蔽词列表（运营维护）

**3. 后台线程处理**
- `ProcessWorker(threading.Thread)` — 不阻塞 GUI
- 支持暂停/恢复/停止
- 进度回调实时更新 UI

---

## Slide 11 — 测试策略

**测试分层：**

| 层级 | 内容 | 方式 |
|------|------|------|
| **模块导入测试** | 所有模块能正常 import | `test_app.py` |
| **适配器单测** | 每个 API 适配器的请求构造和响应解析 | `test_linkapi.py` |
| **工作流集成测试** | 完整流程：加载图片 → API 调用 → 输出验证 | `test_linkapi_workflow.py` |
| **格式对比测试** | 不同请求格式的兼容性验证 | `test_format_comparison.py` |

**测试方法：**
- 创建临时测试图片（PIL 生成白底+文字）
- 调用 API 处理
- 验证输出文件存在且尺寸合理
- 测试完成后清理临时文件

**调试手段：**
- API 完整响应打印（`[调试] API 完整响应: ...`）
- API Key 脱敏显示（`sk-681b...`）
- 处理报告 JSON 记录每张图的模型/耗时/结果

---

## Slide 12 — 关键数据结构

**核心数据类：**

```python
@dataclass
class FileListItem:
    file_path: str           # 图片路径
    filename: str            # 文件名
    status: str = "等待"     # 等待/处理中/完成/失败
    model: str = "..."       # 每图独立模型
    prompt: str = ""         # 每图独立提示词
    is_reference: bool = False  # 是否为参考图

@dataclass
class ProcessingResult:
    success: bool
    image: Optional[Image.Image]
    message: str
```

**处理报告 (report.json)：**
```json
{
  "report_info": {
    "total_images": 10,
    "success_count": 8,
    "failed_count": 2
  },
  "model_statistics": {
    "gemini-3-pro-image-preview": {"total": 5, "success": 5},
    "gemini-2.5-flash-image": {"total": 5, "success": 3}
  },
  "results": [...]
}
```

---

## Slide 13 — 服务商对比

| 维度 | Google Gemini | NanoBanana | LinkAPI.ai | BananaPro |
|------|:---:|:---:|:---:|:---:|
| 本地文件 | ✅ | ❌ URL only | ✅ | ✅ |
| 处理模式 | 同步 | 异步轮询 | 同步 | 同步 |
| 认证方式 | API Key(query) | Bearer Token | x-goog-api-key | Bearer Token |
| 内容限制 | 严格 | 宽松 | 中等 | 中等 |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## Slide 14 — 经验总结

**做得好的地方：**
- 适配器模式让多服务商切换变得简单，新增服务商 < 300 行代码
- 模板系统设计合理，默认模板保护 + 自定义模板灵活
- 每图独立配置（模型 + 模板）满足了实际业务需求
- 处理报告 JSON 格式清晰，方便后续数据分析

**踩过的坑：**
- Gemini API 返回驼峰 `inlineData` 不是下划线 `inline_data`，花了时间排查
- 中转站 API 文档和实际行为不一致（认证方式），**永远要实测**
- 输出文件夹被占用（Explorer 锁定），加了 3 次重试机制
- tkinter Canvas 滚动在不同分辨率下表现不一致

**未来方向：**
- 处理预览（先预览再保存）
- 断点续传（大批量处理中断后可恢复）
- 更多服务商接入（Seedream、Wan API）

---

## Slide 15 — Q&A

**感谢聆听**
