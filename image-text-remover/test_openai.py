"""测试 OpenAI GPT Image adapter 是否能通过 BananaPro 中转调用"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import io
from PIL import Image, ImageDraw

# 创建一个简单的测试图片（白底带文字）
img = Image.new("RGB", (400, 200), "white")
draw = ImageDraw.Draw(img)
draw.text((100, 80), "TEST 123", fill="black")
test_path = Path("input") / "test_image.jpg"
test_path.parent.mkdir(exist_ok=True)
img.save(str(test_path), quality=95)
print(f"[1] 测试图片已创建: {test_path}")

# 读取配置
from core.config import get_config
config = get_config()
oi_config = config.get_openai_config()
api_key = oi_config.get("api_key", "")
base_url = oi_config.get("base_url", "")
model = oi_config.get("model", "gpt-image-2")

print(f"[2] 配置读取: key={api_key[:12]}...{api_key[-4:]}, base_url={base_url}, model={model}")

# 测试 adapter
from core.openai_adapter import OpenAIImageAdapter
adapter = OpenAIImageAdapter(api_key, model, base_url=base_url)
print(f"[3] Adapter URL: {adapter.base_url}")

print(f"[4] 开始调用 API...")
result = adapter.process_image(
    str(test_path),
    "Remove the text from this image while keeping the background clean."
)

if result.success:
    out_path = Path("output") / "test_openai_result.jpg"
    out_path.parent.mkdir(exist_ok=True)
    result.image.convert("RGB").save(str(out_path), quality=95)
    print(f"[5] ✅ 成功! 结果已保存: {out_path}")
else:
    print(f"[5] ❌ 失败: {result.message}")
