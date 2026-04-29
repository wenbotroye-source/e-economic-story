# LinkAPI.ai 接口使用说明

## 概述
已成功集成 LinkAPI.ai 图像处理接口到 image-text-remover 项目中。该接口支持提示词 + 图片格式的输入，输出处理后的图片。

## 功能特性
- ✅ 输入：提示词 + 本地图片文件
- ✅ 自动将本地图片转换为 base64 格式上传
- ✅ 支持多种 Gemini 模型（推荐：gemini-2.5-flash-image）
- ✅ 自动将 API 返回的 base64 转换为 JPG 格式
- ✅ 完整的错误处理和进度回调

## 使用方式

### 1. GUI 界面使用
1. 启动修图工具：`启动工具.bat`
2. 在左侧配置面板选择服务商：**LinkAPI.ai**
3. 填入 LinkAPI.ai API Key
4. 添加图片并开始处理

### 2. 代码调用
```python
from core.linkapi_adapter import LinkAPIAdapter, process_with_linkapi

# 方式1：使用便捷函数
result = process_with_linkapi(
    image_path="input/image.jpg",
    api_key="sk-...",
    prompt="Clean up the image by removing text overlays and signatures. Keep the product intact."
)

# 方式2：使用适配器类
adapter = LinkAPIAdapter(api_key="sk-...", model="gemini-2.5-flash-image")
result = adapter.process_image("input/image.jpg", "你的提示词")

if result.success:
    result.image.save("output/result.jpg")
```

### 3. 工作流集成
```python
from core.workflow import TextRemovalWorkflow

workflow = TextRemovalWorkflow(
    api_key="sk-...",
    provider="linkapi",
    model="gemini-2.5-flash-image"
)

result = workflow.process(
    image_input="input/image.jpg",
    output_path="output/result.jpg",
    prompt="Clean up the image by removing text overlays and signatures. Keep the product intact."
)
```

## 配置说明

### API Key 获取
- 访问 https://linkapi.ai
- 注册账号并获取 API Key
- 格式：`sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 推荐模型
- `gemini-2.5-flash-image` - 速度最快，推荐使用
- `gemini-3.1-flash-image-preview` - 平衡型
- `gemini-3-pro-image-preview` - 质量最高（可能有函数调用限制）

### Prompt 建议
**推荐使用安全的提示词，避免触发 API 的函数调用机制：**

✅ 推荐：
- "Clean up the image by removing text overlays and signatures. Keep the product intact."
- "Remove all visible text and annotations from the image while preserving the product."

❌ 避免：
- "Remove watermarks" - 可能触发安全限制
- "Remove logos" - 可能触发商标相关限制
- 包含 "segment"、"detect" 等词汇的提示词

## 技术细节

### 输入处理
1. 加载本地图片文件
2. 转换为 RGB 模式（去除 alpha 通道）
3. 压缩为 JPEG 格式（质量 95%）
4. Base64 编码

### API 调用
- 端点：`https://linkapi.ai/v1beta/models/{model}:generateContent`
- 认证：`x-goog-api-key` 头
- 超时：300 秒（5分钟）
- 格式：Google Gemini 兼容格式

### 输出处理
1. 解析 API 响应
2. 提取 base64 图片数据
3. 解码为 PIL Image 对象
4. 保存为 JPG 文件（可配置质量）

## 错误处理

### 常见问题
1. **MALFORMED_FUNCTION_CALL**: Prompt 触发了 API 的函数调用机制
   - 解决方案：使用更简单的提示词

2. **NO_IMAGE**: API 认为输入图片无需处理
   - 解决方案：返回原始图片

3. **超时**: 网络连接问题
   - 解决方案：检查网络连接，API 已设置 300 秒超时

## 文件结构
```
core/
├── linkapi_adapter.py     # LinkAPI.ai 适配器（新创建）
├── api_adapter.py         # 更新：添加 LinkAPIAdapter 集成
├── workflow.py            # 更新：支持 LinkAPI.ai 工作流
└── config.py              # 更新：添加 LinkAPI.ai 配置方法

gui/
└── config_panel.py        # 更新：添加 LinkAPI.ai 选项

providers.yaml             # 更新：添加 LinkAPI.ai 配置

test_linkapi*.py           # 测试文件
```

## 测试验证
所有测试已通过：
- ✅ `test_linkapi_simple.py` - 基础 API 连接测试
- ✅ `test_linkapi.py` - 完整适配器功能测试
- ✅ `test_adapter_steps.py` - 分步调试测试
- ✅ `test_format_comparison.py` - 请求格式验证
- ✅ `test_linkapi_workflow.py` - 工作流集成测试

## 注意事项
1. **模型选择**：推荐使用 `gemini-2.5-flash-image`，避免 `gemini-3-pro-image-preview` 的函数调用限制
2. **Prompt 用词**：避免使用可能触发安全限制的词汇
3. **API Key 安全**：不要在代码中硬编码 API Key，使用配置文件或环境变量
4. **网络连接**：确保能够访问 linkapi.ai 域名