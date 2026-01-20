#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英语单词默写纸生成器 - GUI主窗口
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QCheckBox, QSpinBox, QProgressBar, QTextEdit, QFileDialog,
    QMessageBox, QDialog, QDialogButtonBox, QGroupBox, QScrollArea, QFrame,
    QMenuBar, QMenu
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.generator import DictationGenerator


class GenerateThread(QThread):
    """生成线程，用于异步生成PDF"""

    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, object)

    def __init__(self, generator: DictationGenerator, units: List[str],
                 count: Optional[int], copies: int, word_types: List[str],
                 output_dir: str):
        super().__init__()
        self.generator = generator
        self.units = units
        self.count = count
        self.copies = copies
        self.word_types = word_types
        self.output_dir = output_dir
        self.generated_files = []

    def run(self):
        try:
            # 生成多份默写纸
            for copy_num in range(1, self.copies + 1):
                self.progress_signal.emit(f"正在生成第 {copy_num}/{self.copies} 份...")

                # 随机抽取单词
                words = self.generator.get_words_by_units(
                    self.units, self.count, self.word_types
                )

                if not words:
                    self.progress_signal.emit(
                        f"警告：没有找到符合条件的单词（单元：{self.units}，类型：{self.word_types}）"
                    )
                    continue

                # 生成文件名
                unit_str = '_'.join(self.units)
                date_str = datetime.now().strftime('%Y%m%d')
                output_file = str(
                    Path(self.output_dir) / f'默写纸_{unit_str}_{date_str}_{copy_num:02d}.pdf'
                )

                # 生成PDF
                self.generator.generate_pdf(words, output_file, unit_str)
                self.generated_files.append(output_file)

            self.progress_signal.emit(f"✓ 完成！共生成 {len(self.generated_files)} 份默写纸")
            self.finished_signal.emit(True, "生成成功！", self.generated_files)

        except Exception as e:
            error_msg = f"生成失败：{str(e)}"
            self.progress_signal.emit(f"✗ {error_msg}")
            self.finished_signal.emit(False, error_msg, [])


class PreviewDialog(QDialog):
    """预览对话框"""

    def __init__(self, parent=None, generator: DictationGenerator = None,
                 units: List[str] = None, word_types: List[str] = None,
                 count: Optional[int] = None, copies: int = 1,
                 output_dir: str = None):
        super().__init__(parent)
        self.generator = generator
        self.units = units or []
        self.word_types = word_types or []
        self.count = count
        self.copies = copies
        self.output_dir = output_dir
        self.init_ui()
        self.load_preview_data()

    def init_ui(self):
        self.setWindowTitle("生成预览")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        # 已选择单元
        layout.addWidget(QLabel(f"<b>已选择单元:</b> {', '.join(self.units)}"))
        layout.addWidget(QLabel(f"<b>已选择类型:</b> {', '.join(self.word_types)}"))
        layout.addSpacing(10)

        # 词汇统计
        stats_group = QGroupBox("词汇统计")
        stats_layout = QVBoxLayout()

        total_count = 0
        for word_type in ['单词', '短语', '句子']:
            count = 0
            for unit in self.units:
                count += self.generator.get_word_count_by_unit(unit, word_type)
            if count > 0:
                stats_layout.addWidget(QLabel(f"  • {word_type}: {count} 个"))
                total_count += count

        stats_layout.addWidget(QLabel(f"  • 总计: {total_count} 个"))
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # 生成配置
        config_group = QGroupBox("生成配置")
        config_layout = QVBoxLayout()

        count_text = f"{self.count} 个（随机）" if self.count else "全部"
        config_layout.addWidget(QLabel(f"  • 抽取数量: {count_text}"))
        config_layout.addWidget(QLabel(f"  • 生成份数: {self.copies} 份"))
        config_layout.addWidget(QLabel(f"  • 输出位置: {self.output_dir}"))
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def load_preview_data(self):
        """加载预览数据"""
        pass


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.generator: Optional[DictationGenerator] = None
        self.unit_checkboxes: List[QCheckBox] = []
        self.grade_checkboxes: List[QCheckBox] = []
        self.type_checkboxes: List[QCheckBox] = []
        self.generate_thread: Optional[GenerateThread] = None
        self.init_ui()
        self.load_default_data()

    def init_ui(self):
        self.setWindowTitle("英语默写纸生成器")
        self.setMinimumSize(800, 700)

        # 创建菜单栏
        menubar = self.menuBar()
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        about_action = help_menu.addAction("关于(&A)")
        about_action.triggered.connect(self.show_about)

        # 主窗口部件
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout()

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        # ========== 数据源设置 ==========
        data_group = QGroupBox("数据源设置")
        data_layout = QVBoxLayout()

        # CSV文件路径
        csv_layout = QHBoxLayout()
        csv_layout.addWidget(QLabel("CSV文件路径:"))
        self.csv_path_edit = QLineEdit()
        self.csv_path_edit.setPlaceholderText("选择CSV文件...")
        csv_layout.addWidget(self.csv_path_edit)
        csv_browse_btn = QPushButton("浏览...")
        csv_browse_btn.clicked.connect(self.browse_csv_file)
        csv_layout.addWidget(csv_browse_btn)
        data_layout.addLayout(csv_layout)

        # 年级选择
        data_layout.addWidget(QLabel("年级选择:"))
        self.grades_layout = QHBoxLayout()
        data_layout.addLayout(self.grades_layout)

        # 单元选择
        data_layout.addWidget(QLabel("可用单元:"))
        self.units_layout = QHBoxLayout()
        data_layout.addLayout(self.units_layout)

        # 默写类型
        data_layout.addWidget(QLabel("默写类型:"))
        self.types_layout = QHBoxLayout()
        data_layout.addLayout(self.types_layout)

        data_group.setLayout(data_layout)
        scroll_layout.addWidget(data_group)

        # ========== 生成设置 ==========
        generate_group = QGroupBox("生成设置")
        generate_layout = QVBoxLayout()

        # 抽取数量
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("抽取数量:"))
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setMinimum(1)
        self.count_spinbox.setMaximum(1000)
        self.count_spinbox.setValue(15)
        self.count_spinbox.setSpecialValueText("全部")
        count_layout.addWidget(self.count_spinbox)
        count_layout.addWidget(QLabel(" 个（0表示生成全部）"))
        generate_layout.addLayout(count_layout)

        # 生成份数
        copies_layout = QHBoxLayout()
        copies_layout.addWidget(QLabel("生成份数:"))
        self.copies_spinbox = QSpinBox()
        self.copies_spinbox.setMinimum(1)
        self.copies_spinbox.setMaximum(50)
        self.copies_spinbox.setValue(1)
        copies_layout.addWidget(self.copies_spinbox)
        copies_layout.addWidget(QLabel(" 份（每份随机抽取）"))
        generate_layout.addLayout(copies_layout)

        # 输出目录
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录...")
        output_layout.addWidget(self.output_dir_edit)
        output_browse_btn = QPushButton("浏览...")
        output_browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(output_browse_btn)
        generate_layout.addLayout(output_layout)

        generate_group.setLayout(generate_layout)
        scroll_layout.addWidget(generate_group)

        # ========== 操作按钮 ==========
        button_layout = QHBoxLayout()
        self.preview_btn = QPushButton("预览设置")
        self.preview_btn.clicked.connect(self.preview_settings)
        button_layout.addWidget(self.preview_btn)

        self.generate_btn = QPushButton("生成默写纸")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_dictation)
        button_layout.addWidget(self.generate_btn)
        scroll_layout.addLayout(button_layout)

        # ========== 进度显示 ==========
        progress_group = QGroupBox("生成进度")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        progress_layout.addWidget(self.status_label)

        progress_group.setLayout(progress_layout)
        scroll_layout.addWidget(progress_group)

        # ========== 输出日志 ==========
        log_group = QGroupBox("输出日志")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        scroll_layout.addWidget(log_group)

        # 打开输出文件夹按钮
        self.open_folder_btn = QPushButton("打开输出文件夹")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setEnabled(False)
        scroll_layout.addWidget(self.open_folder_btn)

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        widget.setLayout(layout)

    def load_default_data(self):
        """加载默认数据"""
        # 设置默认CSV文件路径
        default_csv = Path(__file__).parent.parent / "data" / "校内英语单词.csv"
        if default_csv.exists():
            self.csv_path_edit.setText(str(default_csv))
            self.load_csv_data(default_csv)

        # 设置默认输出目录
        self.output_dir_edit.setText(str(Path.home() / "Desktop"))

    def load_csv_data(self, csv_path: Path):
        """加载CSV数据"""
        try:
            self.generator = DictationGenerator(str(csv_path))
            self.generator.load_vocabulary()

            # 清除旧的年级复选框
            for checkbox in self.grade_checkboxes:
                checkbox.deleteLater()
            self.grade_checkboxes.clear()

            # 创建新的年级复选框
            grades = self.generator.get_available_grades()
            for grade in grades:
                checkbox = QCheckBox(grade)
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(self.on_grade_changed)
                self.grade_checkboxes.append(checkbox)
                self.grades_layout.addWidget(checkbox)

            # 清除旧的单元复选框
            for checkbox in self.unit_checkboxes:
                checkbox.deleteLater()
            self.unit_checkboxes.clear()

            # 创建新的单元复选框（基于选中的年级）
            self.update_unit_checkboxes()

            # 清除旧的类型复选框
            for checkbox in self.type_checkboxes:
                checkbox.deleteLater()
            self.type_checkboxes.clear()

            # 创建类型复选框
            for word_type in ['单词', '短语', '句子']:
                checkbox = QCheckBox(word_type)
                checkbox.setChecked(True)
                self.type_checkboxes.append(checkbox)
                self.types_layout.addWidget(checkbox)

            self.log(f"✓ 已加载 {len(self.generator.vocabulary)} 个词汇")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载CSV文件失败：{str(e)}")
            self.log(f"✗ 加载CSV文件失败：{str(e)}")

    def on_grade_changed(self):
        """年级选择变化时更新单元列表"""
        self.update_unit_checkboxes()

    def update_unit_checkboxes(self):
        """根据选中的年级更新单元复选框"""
        # 获取选中的年级
        selected_grades = [cb.text() for cb in self.grade_checkboxes if cb.isChecked()]

        # 获取选中年级的所有单元
        available_units = set()
        for grade in selected_grades:
            units = self.generator.get_units_by_grade(grade)
            available_units.update(units)

        # 清除旧的单元复选框
        for checkbox in self.unit_checkboxes:
            checkbox.deleteLater()
        self.unit_checkboxes.clear()

        # 创建新的单元复选框
        for unit in sorted(available_units):
            checkbox = QCheckBox(unit)
            checkbox.setChecked(True)
            self.unit_checkboxes.append(checkbox)
            self.units_layout.addWidget(checkbox)

    def browse_csv_file(self):
        """浏览CSV文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", "", "CSV文件 (*.csv)"
        )
        if file_path:
            self.csv_path_edit.setText(file_path)
            self.load_csv_data(Path(file_path))

    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def get_selected_units(self) -> List[str]:
        """获取选中的单元"""
        return [cb.text() for cb in self.unit_checkboxes if cb.isChecked()]

    def get_selected_types(self) -> List[str]:
        """获取选中的类型"""
        return [cb.text() for cb in self.type_checkboxes if cb.isChecked()]

    def preview_settings(self):
        """预览设置"""
        if not self.generator:
            QMessageBox.warning(self, "警告", "请先选择CSV文件")
            return

        units = self.get_selected_units()
        if not units:
            QMessageBox.warning(self, "警告", "请至少选择一个单元")
            return

        word_types = self.get_selected_types()
        if not word_types:
            QMessageBox.warning(self, "警告", "请至少选择一个单词类型")
            return

        count = self.count_spinbox.value()
        if count == 0:
            count = None

        copies = self.copies_spinbox.value()
        output_dir = self.output_dir_edit.text()

        dialog = PreviewDialog(
            self, self.generator, units, word_types, count, copies, output_dir
        )
        dialog.exec()

    def generate_dictation(self):
        """生成默写纸"""
        if not self.generator:
            QMessageBox.warning(self, "警告", "请先选择CSV文件")
            return

        units = self.get_selected_units()
        if not units:
            QMessageBox.warning(self, "警告", "请至少选择一个单元")
            return

        word_types = self.get_selected_types()
        if not word_types:
            QMessageBox.warning(self, "警告", "请至少选择一个单词类型")
            return

        count = self.count_spinbox.value()
        if count == 0:
            count = None

        copies = self.copies_spinbox.value()
        output_dir = self.output_dir_edit.text()

        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return

        # 禁用生成按钮
        self.generate_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        # 创建生成线程
        self.generate_thread = GenerateThread(
            self.generator, units, count, copies, word_types, output_dir
        )
        self.generate_thread.progress_signal.connect(self.update_progress)
        self.generate_thread.finished_signal.connect(self.on_generate_finished)
        self.generate_thread.start()

    def update_progress(self, message: str):
        """更新进度"""
        self.status_label.setText(message)
        self.log(message)

        # 更新进度条（简单估算）
        if "正在生成第" in message:
            parts = message.split("/")
            if len(parts) == 2:
                current = int(parts[0].split()[-1])
                total = int(parts[1].split()[0])
                progress = int((current / total) * 100)
                self.progress_bar.setValue(progress)

    def on_generate_finished(self, success: bool, message: str, files: List[str]):
        """生成完成"""
        self.generate_btn.setEnabled(True)

        if success:
            self.progress_bar.setValue(100)
            self.open_folder_btn.setEnabled(True)
            QMessageBox.information(self, "成功", message)
        else:
            self.progress_bar.setValue(0)
            QMessageBox.critical(self, "错误", message)

    def open_output_folder(self):
        """打开输出文件夹"""
        output_dir = self.output_dir_edit.text()
        if not output_dir:
            return

        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', output_dir])
            elif sys.platform == 'win32':  # Windows
                subprocess.run(['explorer', output_dir])
            else:  # Linux
                subprocess.run(['xdg-open', output_dir])
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法打开文件夹：{str(e)}")

    def log(self, message: str):
        """添加日志"""
        self.log_text.append(message)
        # 自动滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>英语默写纸生成器</h2>
        <p><b>版本：</b>2.0</p>
        <p><b>作者：</b>俞博衍教育</p>
        <hr>
        <p>从CSV文件中抽取英语单词、短语和句子，生成PDF格式的默写纸。</p>
        <p>适用于小学生英语学习，采用标准英文练习本样式。</p>
        """
        QMessageBox.about(self, "关于", about_text)