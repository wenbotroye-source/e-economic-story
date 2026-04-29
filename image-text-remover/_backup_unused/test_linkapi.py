#!/usr/bin/env python3
"""
测试 LinkAPI.ai 适配器
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.linkapi_adapter import LinkAPIAdapter, process_with_linkapi
from PIL import Image

def test_linkapi_adapter():
    """测试 LinkAPI.ai 适配器"""
    print("=" * 60)
    print("测试 LinkAPI.ai 适配器")
    print("=" * 60)

    # API 配置
    API_KEY = "sk-OYgGPxBYShs7halE6A2dZR8iaOgRrIoNZqqpGqCzG5upijVl"
    MODEL = "gemini-2.5-flash-image"  # 使用更简单的模型

    # 测试图片路径（使用项目中的示例图片或创建一个测试图片）
    test_image_path = project_root / "input" / "test.jpg"

    # 如果测试图片不存在，创建一个简单的测试图片
    if not test_image_path.exists():
        print("创建测试图片...")
        test_image_path.parent.mkdir(exist_ok=True)

        # 创建一个简单的测试图片
        img = Image.new('RGB', (800, 600), color='white')
        # 添加一些文字模拟（用不同颜色的矩形）
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 700, 200], fill='lightblue', outline='blue')
        draw.text((200, 130), "TEST WATERMARK TEXT", fill='black')
        img.save(test_image_path)
        print(f"测试图片已创建: {test_image_path}")

    # 测试提示词
    prompt = "Clean up the image by removing text overlays and signatures. Keep the product intact."

    try:
        print(f"\n1. 测试直接函数调用...")
        print(f"   图片路径: {test_image_path}")
        print(f"   提示词: {prompt}")
        print(f"   模型: {MODEL}")

        # 测试便捷函数
        result = process_with_linkapi(
            image_path=str(test_image_path),
            api_key=API_KEY,
            prompt=prompt,
            model=MODEL
        )

        if result.success:
            print("   [OK] 处理成功！")

            # 保存结果
            output_path = project_root / "output" / "linkapi_test_result.jpg"
            output_path.parent.mkdir(exist_ok=True)
            result.image.save(output_path)
            print(f"   结果已保存: {output_path}")

            # 显示图片信息
            print(f"   输出图片尺寸: {result.image.size}")
            print(f"   输出图片模式: {result.image.mode}")
        else:
            print(f"   [ERROR] 处理失败: {result.message}")
            return False

        print(f"\n2. 测试适配器类直接调用...")
        adapter = LinkAPIAdapter(API_KEY, MODEL)

        # 测试图片加载和base64编码
        input_image = adapter._load_image(str(test_image_path))
        if input_image:
            print("   [OK] 图片加载成功")
            image_base64, mime_type = adapter._image_to_base64(input_image)
            print(f"   [OK] Base64编码成功，MIME类型: {mime_type}")
            print(f"   Base64长度: {len(image_base64)} 字符")
        else:
            print("   [ERROR] 图片加载失败")
            return False

        print(f"\n3. 测试完整处理流程...")
        result2 = adapter.process_image(
            image_path=str(test_image_path),
            prompt=prompt
        )

        if result2.success:
            print("   [OK] 完整处理流程成功！")

            # 保存第二个结果
            output_path2 = project_root / "output" / "linkapi_test_result2.jpg"
            result2.image.save(output_path2)
            print(f"   结果已保存: {output_path2}")
        else:
            print(f"   [ERROR] 完整处理流程失败: {result2.message}")
            return False

        print(f"\n" + "=" * 60)
        print("[SUCCESS] 所有测试通过！LinkAPI.ai 适配器工作正常。")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_linkapi_adapter()
    sys.exit(0 if success else 1)