#!/usr/bin/env python3
"""
测试 LinkAPI.ai 在工作流中的集成
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.workflow import TextRemovalWorkflow
from PIL import Image, ImageDraw

def test_linkapi_workflow():
    """测试 LinkAPI.ai 工作流集成"""
    print("=" * 60)
    print("测试 LinkAPI.ai 工作流集成")
    print("=" * 60)

    API_KEY = "sk-OYgGPxBYShs7halE6A2dZR8iaOgRrIoNZqqpGqCzG5upijVl"

    # 创建测试图片
    print("1. 创建测试图片...")
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 150], fill='lightblue', outline='blue', width=2)
    draw.text((100, 90), "TEST TEXT", fill='black')

    test_image_path = project_root / "input" / "test_workflow.jpg"
    test_image_path.parent.mkdir(exist_ok=True)
    img.save(test_image_path)
    print(f"   测试图片已创建: {test_image_path}")

    try:
        # 创建 LinkAPI.ai 工作流
        print("2. 创建 LinkAPI.ai 工作流...")
        workflow = TextRemovalWorkflow(
            api_key=API_KEY,
            provider="linkapi",
            model="gemini-2.5-flash-image"
        )
        print("   [OK] 工作流创建成功")

        # 处理图片
        print("3. 处理图片...")
        output_path = project_root / "output" / "workflow_test_result.jpg"
        output_path.parent.mkdir(exist_ok=True)

        result = workflow.process(
            image_input=str(test_image_path),
            output_path=str(output_path),
            prompt="Clean up the image by removing text overlays and signatures. Keep the product intact."
        )

        if result.success:
            print("   [OK] 处理成功！")
            print(f"   结果已保存: {output_path}")

            # 验证输出文件
            if output_path.exists():
                output_img = Image.open(output_path)
                print(f"   输出图片尺寸: {output_img.size}")
                print(f"   输出图片模式: {output_img.mode}")
            else:
                print("   [ERROR] 输出文件不存在")
                return False
        else:
            print(f"   [ERROR] 处理失败: {result.message}")
            return False

        print(f"\n" + "=" * 60)
        print("[SUCCESS] LinkAPI.ai 工作流集成测试通过！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试文件
        if test_image_path.exists():
            test_image_path.unlink()
            print(f"\n清理测试文件: {test_image_path}")

if __name__ == "__main__":
    success = test_linkapi_workflow()
    sys.exit(0 if success else 1)