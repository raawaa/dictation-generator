#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英语单词默写纸生成器 - GUI入口
"""

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格

    window = MainWindow()
    window.setWindowTitle('英语单词默写纸生成器 v2.0')
    window.resize(800, 700)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()