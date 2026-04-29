#!/usr/bin/env python3
"""
测试适配器的图片处理流程
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.linkapi_adapter import LinkAPIAdapter
from PIL import Image

def test_adapter_step_by_step():
    """逐步测试适配器"""
    print("=" * 60)
    print("逐步测试 LinkAPI.ai 适配器")
    print("=" * 60)

    API_KEY = "sk-OYgGPxBYShs7halE6A2dZR8iaOgRrIoNZqqpGqCzG5upijVl"
    MODEL = "gemini-2.5-flash-image"

    # 使用之前创建的测试图片
    test_image_path = project_root / "input" / "test.jpg"

    if not test_image_path.exists():
        print("错误: 测试图片不存在")
        return False

    adapter = LinkAPIAdapter(API_KEY, MODEL)

    try:
        # 步骤1: 加载图片
        print("1. 测试图片加载...")
        input_image = adapter._load_image(str(test_image_path))
        if input_image:
            print(f"   [OK] 图片加载成功: {input_image.size}, {input_image.mode}")
        else:
            print("   [ERROR] 图片加载失败")
            return False

        # 步骤2: Base64编码
        print("2. 测试Base64编码...")
        image_base64, mime_type = adapter._image_to_base64(input_image)
        print(f"   [OK] Base64编码成功")
        print(f"   MIME类型: {mime_type}")
        print(f"   Base64长度: {len(image_base64)} 字符")

        # 步骤3: 构建请求
        print("3. 测试请求构建...")
        prompt = "Clean up the image by removing text overlays and signatures. Keep the product intact."

        request_data = {
            "contents": [{
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_base64
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }

        print(f"   [OK] 请求构建成功")
        print(f"   请求数据大小: {len(str(request_data))} 字符")

        # 步骤4: 发送请求
        print("4. 测试API调用...")
        result_image = adapter._call_linkapi_api(image_base64, mime_type, prompt, input_image)

        if result_image:
            print(f"   [OK] API调用成功")
            print(f"   结果图片尺寸: {result_image.size}")
            print(f"   结果图片模式: {result_image.mode}")

            # 保存结果
            output_path = project_root / "output" / "adapter_test_result.jpg"
            output_path.parent.mkdir(exist_ok=True)
            result_image.save(output_path)
            print(f"   结果已保存: {output_path}")
            return True
        else:
            print("   [ERROR] API调用失败")
            return False

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_adapter_step_by_step()
    print(f"\n测试结果: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1)