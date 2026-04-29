#!/usr/bin/env python3
"""
打包脚本 - 使用PyInstaller生成exe

使用方法:
    python build_exe.py

打包后文件在 dist/ 目录下
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path


def clean_build():
    """清理构建文件"""
    print("[清理] 清理构建文件...")
    dirs_to_remove = ['build', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"   删除 {dir_name}/")
            except PermissionError:
                print(f"   跳过 {dir_name}/ (被占用)")

    # 清理pyc文件
    for pyc in Path('.').rglob('*.pyc'):
        pyc.unlink()
    for pycache in Path('.').rglob('__pycache__'):
        if pycache.is_dir():
            shutil.rmtree(pycache)


def get_platform_specific_separator():
    """获取平台特定的路径分隔符"""
    return ';' if platform.system() == 'Windows' else ':'


def get_app_name():
    """获取平台特定的应用程序名称"""
    system = platform.system()
    if system == 'Windows':
        return '修图工具'
    elif system == 'Darwin':  # macOS
        return 'ImageTextRemover'
    else:  # Linux
        return 'image-text-remover'


def build_exe():
    """构建exe"""
    print("[构建] 开始打包...")

    separator = get_platform_specific_separator()
    app_name = get_app_name()

    # PyInstaller参数
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', app_name,
        '--windowed',  # GUI模式，不显示控制台
        '--onefile',   # 打包成单个文件
        '--clean',     # 清理临时文件
        '--noconfirm', # 不确认覆盖

        # 添加数据文件（使用平台特定分隔符）
        '--add-data', f'core{separator}core',
        '--add-data', f'config{separator}config',
        '--add-data', f'gui{separator}gui',
        '--add-data', f'providers.yaml{separator}.',

        # 隐藏导入
        '--hidden-import', 'PIL._tkinter_finder',
        '--hidden-import', 'requests',
        '--hidden-import', 'yaml',

        # 主入口文件
        'gui_app.py'
    ]

    # macOS特定配置
    if platform.system() == 'Darwin':
        cmd.extend([
            '--osx-bundle-identifier', 'com.imagetextremover.app',
        ])

    print(f"   执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("[错误] 打包失败!")
        return False

    print("[成功] 打包成功!")
    return True


def copy_additional_files():
    """复制额外文件到dist目录"""
    print("[复制] 复制额外文件...")

    dist_dir = Path('dist')

    # 创建必要的目录
    (dist_dir / 'input').mkdir(exist_ok=True)
    (dist_dir / 'output').mkdir(exist_ok=True)
    (dist_dir / 'config').mkdir(exist_ok=True)

    # 复制配置文件
    if Path('providers.yaml').exists():
        shutil.copy('providers.yaml', dist_dir / 'providers.yaml')
        print("   复制 providers.yaml")

    # 复制屏蔽词列表
    if Path('config/blocklist.txt').exists():
        shutil.copy('config/blocklist.txt', dist_dir / 'config/blocklist.txt')
        print("   复制 blocklist.txt")

    print("[成功] 文件复制完成")


def create_macos_app_bundle():
    """为macOS创建.app bundle"""
    if platform.system() != 'Darwin':
        return

    print("[macOS] 创建.app bundle...")

    app_name = get_app_name()
    dist_dir = Path('dist')
    app_path = dist_dir / f'{app_name}.app'

    # 如果.app已存在，先删除
    if app_path.exists():
        shutil.rmtree(app_path)

    # 创建基本的.app结构
    contents_dir = app_path / 'Contents'
    macos_dir = contents_dir / 'MacOS'
    resources_dir = contents_dir / 'Resources'

    macos_dir.mkdir(parents=True)
    resources_dir.mkdir(parents=True)

    # 复制可执行文件
    exe_path = dist_dir / app_name
    if exe_path.exists():
        shutil.copy(exe_path, macos_dir / app_name)
        os.chmod(macos_dir / app_name, 0o755)

    # 创建Info.plist
    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundleDisplayName</key>
    <string>图片文字去除工具</string>
    <key>CFBundleIdentifier</key>
    <string>com.imagetextremover.app</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>{app_name}</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>"""

    with open(contents_dir / 'Info.plist', 'w', encoding='utf-8') as f:
        f.write(info_plist)

    print(f"[macOS] 创建 {app_name}.app bundle 完成")


def create_readme():
    """创建使用说明"""
    system = platform.system()
    if system == 'Windows':
        exe_name = '修图工具.exe'
    elif system == 'Darwin':
        exe_name = f'{get_app_name()}.app'
    else:
        exe_name = get_app_name()

    readme_content = f"""# 修图工具

## 使用方法

1. **配置API**
   - 运行 `{exe_name}`
   - 在左侧填写API Key
   - 选择处理模式

2. **添加图片**
   - 点击"添加图片"或"添加文件夹"
   - 支持 JPG、PNG、WebP 格式

3. **开始处理**
   - 点击"开始处理"按钮
   - 等待处理完成

4. **查看结果**
   - 处理完成后点击"打开输出目录"

## 目录说明

- `input/` - 放入待处理的图片
- `output/` - 处理后的图片输出到这里
- `config/` - 配置文件和屏蔽词列表

## 配置文件

- `settings.json` - 保存的API配置和处理参数
- 修改配置后下次启动会自动加载

## 跨平台支持

- Windows: 运行 `{exe_name}`
- macOS: 运行 `{get_app_name()}.app` 或在终端运行 `./ImageTextRemover`
- Linux: 在终端运行 `./{get_app_name()}`
"""

    dist_dir = Path('dist')
    with open(dist_dir / 'README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("[说明] 创建使用说明")


def main():
    """主函数"""
    print("=" * 60)
    print("    修图工具 - 跨平台打包脚本")
    print("=" * 60)
    print(f"    系统: {platform.system()} {platform.release()}")
    print(f"    Python: {sys.version}")
    print("=" * 60)
    print()

    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller 已安装 (版本: {PyInstaller.__version__})")
    except ImportError:
        print("[错误] PyInstaller 未安装")
        print("   请先运行: pip install pyinstaller")
        return

    print()

    # 清理
    clean_build()
    print()

    # 打包
    if not build_exe():
        return

    print()

    # 复制文件
    copy_additional_files()
    print()

    # macOS特定处理
    if platform.system() == 'Darwin':
        create_macos_app_bundle()
        print()

    # 创建说明
    create_readme()
    print()

    print("=" * 60)
    print("[完成] 打包完成!")

    app_name = get_app_name()
    system = platform.system()
    if system == 'Windows':
        print(f"   输出文件: dist/{app_name}.exe")
    elif system == 'Darwin':
        print(f"   输出文件: dist/{app_name}.app")
        print(f"   或直接运行: dist/{app_name}")
    else:
        print(f"   输出文件: dist/{app_name}")

    print("=" * 60)


if __name__ == "__main__":
    main()
