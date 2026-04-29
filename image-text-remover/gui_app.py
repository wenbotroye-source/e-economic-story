#!/usr/bin/env python3
"""
图包去文字工具 - GUI入口

运行方式:
    python gui_app.py
"""

import sys
import os

# 确保可以导入本地模块
if getattr(sys, 'frozen', False):
    # 运行在打包后的exe中
    application_path = os.path.dirname(sys.executable)
else:
    # 运行在普通Python环境中
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

from gui.main_window import main

if __name__ == "__main__":
    main()
