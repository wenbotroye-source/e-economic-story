#!/usr/bin/env python3
"""
图包去文字工具 - 主程序入口

使用方法:
    python main.py --input input_folder --output output_folder
    python main.py --input input_folder --scene white_background
    python main.py --file image.jpg --scene universal
"""

import argparse
import sys
import io
from pathlib import Path

from core.workflow import TextRemovalWorkflow

# 设置标准输出为 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def print_banner():
    """打印欢迎信息"""
    print("""
╔══════════════════════════════════════════╗
║     图包去文字工具 - Ecommerce Cleaner    ║
║         支持 Nano Banana / Seedream        ║
╚══════════════════════════════════════════╝
""")


def progress_callback(message: str, current: int, total: int = 100):
    """进度回调函数"""
    if total == 100:
        # 单文件进度
        bar_length = 30
        filled = int(bar_length * current / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r[{bar}] {current}% {message}", end='', flush=True)
        if current >= 100:
            print()
    else:
        # 批量进度
        print(f"[{current}/{total}] {message}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='去除电商图片中的品牌水印和文字',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 批量处理（自动识别场景）
  python main.py -i ./input -o ./output

  # 强制使用白底图prompt
  python main.py -i ./input -o ./output --scene white_background

  # 使用通用prompt（所有图片一样）
  python main.py -i ./input -o ./output --scene universal

  # 单文件处理
  python main.py -f image.jpg -o output.jpg

场景类型:
  auto             - 自动识别（默认）
  universal        - 使用通用prompt
  white_background - 白底产品图
  lifestyle        - 场景图/生活方式图
  fashion          - 服装/模特
  food             - 食品/美食
  electronics      - 3C/电子产品
        """
    )

    parser.add_argument('-i', '--input', dest='input_dir',
                        help='输入文件夹路径')
    parser.add_argument('-o', '--output', dest='output_dir', default='./output',
                        help='输出文件夹路径 (默认: ./output)')
    parser.add_argument('-f', '--file', dest='single_file',
                        help='单文件处理模式')
    parser.add_argument('--scene', default='auto',
                        help='场景类型 (默认: auto)')
    parser.add_argument('--provider', default=None,
                        help='服务商 (nanobanana 或 gemini)')
    parser.add_argument('--api-key', default=None,
                        help='API Key (可选，否则从配置文件读取)')

    args = parser.parse_args()

    print_banner()

    # 检查参数
    if not args.single_file and not args.input_dir:
        print("❌ 错误: 请指定输入文件 (-f) 或输入文件夹 (-i)")
        parser.print_help()
        sys.exit(1)

    # 处理场景类型
    scene_type = None if args.scene == 'auto' else args.scene

    # 初始化工作流
    print(f"🚀 初始化工作流...")
    print(f"   服务商: {args.provider or '默认 (nanobanana)'}")
    print(f"   场景: {args.scene}")
    print()

    try:
        workflow = TextRemovalWorkflow(
            api_key=args.api_key,
            provider=args.provider or "nanobanana"
        )
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        print("\n💡 提示:")
        print("   1. 检查 providers.yaml 配置文件")
        print("   2. 确保已填写API Key")
        sys.exit(1)

    # 执行处理
    if args.single_file:
        # 单文件模式
        input_file = Path(args.single_file)
        if not input_file.exists():
            print(f"❌ 文件不存在: {input_file}")
            sys.exit(1)

        output_file = Path(args.output_dir) if args.output_dir else input_file.parent / f"{input_file.stem}_clean{input_file.suffix}"

        print(f"📷 处理单文件: {input_file.name}")
        print()

        result = workflow.process(
            str(input_file),
            str(output_file),
            scene_type=scene_type,
            progress_callback=lambda msg, pct: progress_callback(msg, pct)
        )

        print()
        if result.success:
            print(f"✅ 完成!")
            print(f"   输出: {result.output_path}")
            print(f"   检测到 {result.detections_count} 处文字")
            print(f"   去除 {result.removed_count} 处")
        else:
            print(f"❌ 失败: {result.message}")

    else:
        # 批量模式
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir)

        if not input_dir.exists():
            print(f"❌ 输入目录不存在: {input_dir}")
            sys.exit(1)

        print(f"📁 批量处理")
        print(f"   输入: {input_dir.absolute()}")
        print(f"   输出: {output_dir.absolute()}")
        print()

        results = workflow.batch_process(
            str(input_dir),
            str(output_dir),
            scene_type=scene_type,
            progress_callback=progress_callback
        )

        # 统计结果
        success_count = sum(1 for r in results if r.success)
        total_removed = sum(r.removed_count for r in results)
        total_detected = sum(r.detections_count for r in results)

        print()
        print("=" * 50)
        print(f"✅ 处理完成!")
        print(f"   成功: {success_count}/{len(results)}")
        print(f"   总检测: {total_detected} 处文字")
        print(f"   总去除: {total_removed} 处")
        print(f"   输出目录: {output_dir.absolute()}")
        print("=" * 50)


if __name__ == '__main__':
    main()
