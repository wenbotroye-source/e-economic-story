#!/usr/bin/env python3
"""
测试脚本 - 验证image-text-remover功能
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有必要模块是否能正常导入"""
    print("测试模块导入...")

    try:
        import gui.main_window
        print("[OK] gui.main_window 导入成功")
    except Exception as e:
        print(f"[ERROR] gui.main_window 导入失败: {e}")
        return False

    try:
        import core.config
        print("[OK] core.config 导入成功")
    except Exception as e:
        print(f"[ERROR] core.config 导入失败: {e}")
        return False

    try:
        import yaml
        print("[OK] yaml 导入成功")
    except Exception as e:
        print(f"[ERROR] yaml 导入失败: {e}")
        return False

    return True

def test_config():
    """测试配置文件"""
    print("\n测试配置文件...")

    config_path = "providers.yaml"
    if os.path.exists(config_path):
        print(f"[OK] {config_path} 文件存在")

        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print("[OK] 配置文件格式正确")
            print(f"  - 默认OCR: {config.get('default_ocr', '未设置')}")
            print(f"  - 默认修复: {config.get('default_inpaint', '未设置')}")
            return True
        except Exception as e:
            print(f"[ERROR] 配置文件解析失败: {e}")
            return False
    else:
        print(f"[ERROR] {config_path} 文件不存在")
        return False

def test_directories():
    """测试必要目录"""
    print("\n测试目录结构...")

    directories = ['core', 'gui', 'config', 'input', 'output']
    all_exist = True

    for dir_name in directories:
        if os.path.exists(dir_name):
            print(f"[OK] {dir_name}/ 目录存在")
        else:
            print(f"[ERROR] {dir_name}/ 目录不存在")
            all_exist = False

    return all_exist

def main():
    """主测试函数"""
    print("=" * 50)
    print("    image-text-remover 功能测试")
    print("=" * 50)
    print()

    results = []

    # 测试模块导入
    results.append(("模块导入", test_imports()))

    # 测试配置文件
    results.append(("配置文件", test_config()))

    # 测试目录结构
    results.append(("目录结构", test_directories()))

    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 所有测试通过！应用程序可以正常运行。")
        print("\n使用方法:")
        print("1. 运行: 启动工具.bat")
        print("2. 在GUI中配置API密钥")
        print("3. 添加图片并开始处理")
    else:
        print("⚠️  部分测试失败，请检查上述问题。")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)