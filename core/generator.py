#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英语单词默写纸生成器 - 核心逻辑模块
从CSV文件中抽取单词，生成PDF格式的默写纸
"""

import csv
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors


class FourLineGrid(Flowable):
    """英文四线格Flowable"""

    def __init__(self, width=4*cm, height=1.2*cm):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        canvas = self.canv
        line_spacing = 0.3 * cm  # 线间距
        start_y = self.height - line_spacing  # 从顶部开始

        # 绘制四条线
        # 第1条：黑色实线
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.5)
        canvas.line(0, start_y, self.width, start_y)

        # 第2条：黑色实线
        start_y -= line_spacing
        canvas.line(0, start_y, self.width, start_y)

        # 第3条：红色虚线（中间线）
        start_y -= line_spacing
        canvas.setStrokeColor(colors.red)
        canvas.setDash(3, 2)  # 虚线：3实线2空白
        canvas.line(0, start_y, self.width, start_y)

        # 第4条：黑色实线
        start_y -= line_spacing
        canvas.setStrokeColor(colors.black)
        canvas.setDash()  # 取消虚线
        canvas.line(0, start_y, self.width, start_y)


class DictationItem(Flowable):
    """单个默写项（四线格+中文）"""

    def __init__(self, chinese_text, width=4*cm, chinese_font='Helvetica'):
        super().__init__()
        self.chinese_text = chinese_text
        self.width = width
        self.chinese_font = chinese_font
        self.four_line_grid = FourLineGrid(width=width)
        self.height = self.four_line_grid.height + 0.8*cm  # 四线格高度 + 中文高度

    def draw(self):
        canvas = self.canv

        # 绘制四线格
        self.four_line_grid.canv = canvas
        self.four_line_grid.drawOn(canvas, 0, 0.8*cm)

        # 绘制中文
        canvas.setFont(self.chinese_font, 10)
        canvas.setFillColor(colors.black)
        text_width = pdfmetrics.stringWidth(self.chinese_text, self.chinese_font, 10)

        # 居中显示中文
        x = (self.width - text_width) / 2
        canvas.drawString(x, 0.3*cm, self.chinese_text)


class DictationGenerator:
    """默写纸生成器"""

    def __init__(self, csv_file: str, progress_callback: Optional[Callable[[str], None]] = None):
        """
        初始化生成器

        Args:
            csv_file: CSV文件路径
            progress_callback: 进度回调函数，接收状态消息
        """
        self.csv_file = csv_file
        self.vocabulary: List[Dict] = []
        self.unit_dict: Dict[str, List[Dict]] = {}
        self.progress_callback = progress_callback

        # 注册中文字体
        self._register_fonts()

    def _emit_progress(self, message: str):
        """发送进度消息"""
        if self.progress_callback:
            self.progress_callback(message)

    def _register_fonts(self):
        """注册中文字体"""
        # 尝试使用系统自带的中文字体
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',  # macOS
            '/System/Library/Fonts/STHeiti Light.ttc',  # macOS
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Linux
            'C:/Windows/Fonts/msyh.ttc',  # Windows
            'C:/Windows/Fonts/simhei.ttf',  # Windows 黑体
            'C:/Windows/Fonts/simsun.ttc',  # Windows 宋体
        ]

        self.chinese_font = 'Helvetica'
        for font_path in font_paths:
            if Path(font_path).exists():
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    self.chinese_font = 'ChineseFont'
                    break
                except Exception:
                    continue

    def load_vocabulary(self) -> int:
        """
        从CSV文件加载词汇数据

        Returns:
            加载的词汇数量
        """
        self.vocabulary = []
        self.unit_dict = {}

        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.vocabulary.append({
                    'chinese': row['中文'],
                    'english': row['英文'],
                    'unit': row['单元'],
                    'grade': row['年级'],
                    'type': row['类别']
                })

        # 按单元分类
        for word in self.vocabulary:
            unit = word['unit']
            if unit not in self.unit_dict:
                self.unit_dict[unit] = []
            self.unit_dict[unit].append(word)

        self._emit_progress(f"已加载 {len(self.vocabulary)} 个词汇")
        return len(self.vocabulary)

    def get_available_units(self) -> List[str]:
        """获取所有可用的单元"""
        return sorted(self.unit_dict.keys())

    def get_available_grades(self) -> List[str]:
        """获取所有可用的年级"""
        grades = set()
        for word in self.vocabulary:
            grades.add(word['grade'])
        return sorted(grades)

    def get_units_by_grade(self, grade: str) -> List[str]:
        """获取指定年级的所有单元"""
        units = set()
        for word in self.vocabulary:
            if word['grade'] == grade:
                units.add(word['unit'])
        return sorted(units)

    def get_grade_unit_mapping(self) -> Dict[str, List[str]]:
        """获取年级-单元映射关系"""
        mapping = {}
        for word in self.vocabulary:
            grade = word['grade']
            unit = word['unit']
            if grade not in mapping:
                mapping[grade] = set()
            mapping[grade].add(unit)
        return {k: sorted(v) for k, v in mapping.items()}

    def get_word_count_by_unit(self, unit: str, word_type: Optional[str] = None) -> int:
        """
        获取指定单元的单词数量

        Args:
            unit: 单元名称
            word_type: 单词类型（可选）

        Returns:
            单词数量
        """
        if unit not in self.unit_dict:
            return 0

        words = self.unit_dict[unit]
        if word_type:
            if isinstance(word_type, list):
                words = [w for w in words if w['type'] in word_type]
            else:
                words = [w for w in words if w['type'] == word_type]

        return len(words)

    def get_words_by_units(self, units: List[str], count: Optional[int] = None,
                          word_type: Optional[List[str]] = None) -> List[Dict]:
        """
        根据单元获取单词

        Args:
            units: 单元列表，如 ['M1', 'M2']
            count: 需要抽取的单词数量
            word_type: 单词类型列表，如 ['单词', '短语', '句子']

        Returns:
            抽取的单词列表
        """
        words = []
        for unit in units:
            if unit in self.unit_dict:
                unit_words = self.unit_dict[unit]
                if word_type:
                    unit_words = [w for w in unit_words if w['type'] in word_type]
                words.extend(unit_words)

        if count is not None and len(words) > count:
            words = random.sample(words, count)

        return words

    def generate_pdf(self, words: List[Dict], output_file: str, unit_name: str = 'M1'):
        """
        生成PDF默写纸

        Args:
            words: 单词列表
            output_file: 输出文件路径
            unit_name: 单元名称
        """
        self._emit_progress(f"正在生成: {output_file}")

        doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        story = []

        # 添加默写页
        story.extend(self._create_dictation_page(words, unit_name))

        # 添加分页符
        story.append(PageBreak())

        # 添加答案页
        story.extend(self._create_answer_page(words, unit_name))

        # 生成PDF
        doc.build(story)

        self._emit_progress(f"✓ 已生成: {output_file}")

    def _create_dictation_page(self, words: List[Dict], unit_name: str) -> List:
        """创建默写页"""
        elements = []

        # 标题样式
        title_style = ParagraphStyle(
            'Title',
            parent=getSampleStyleSheet()['Title'],
            fontName=self.chinese_font,
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=20
        )

        # 标题
        title = Paragraph(f'英语单词默写 - {unit_name}', title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))

        # 信息行：日期、姓名、分数
        info_style = ParagraphStyle(
            'Info',
            fontName=self.chinese_font,
            fontSize=12,
            spaceAfter=30
        )

        info_text = f'日期：__________  姓名：__________  分数：__________'
        info = Paragraph(info_text, info_style)
        elements.append(info)
        elements.append(Spacer(1, 0.5*cm))

        # 按类型分组单词
        word_items = [w for w in words if w['type'] == '单词']
        non_word_items = [w for w in words if w['type'] != '单词']

        # 添加单词部分
        if word_items:
            elements.append(Paragraph('一、单词', ParagraphStyle(
                'SectionTitle',
                fontName=self.chinese_font,
                fontSize=16,
                spaceAfter=10
            )))
            elements.append(Spacer(1, 0.3*cm))

            # 单词：一行4个
            word_table_data = []
            for i in range(0, len(word_items), 4):
                row = []
                for j in range(4):
                    if i + j < len(word_items):
                        word = word_items[i + j]
                        item = DictationItem(word['chinese'], width=4*cm, chinese_font=self.chinese_font)
                        row.append(item)
                    else:
                        row.append('')
                word_table_data.append(row)

            word_table = Table(word_table_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
            word_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(word_table)
            elements.append(Spacer(1, 0.8*cm))

        # 添加短语和句子部分
        if non_word_items:
            # 按类型分组
            phrase_items = [w for w in non_word_items if w['type'] == '短语']
            sentence_items = [w for w in non_word_items if w['type'] == '句子']

            if phrase_items:
                elements.append(Paragraph('二、短语', ParagraphStyle(
                    'SectionTitle',
                    fontName=self.chinese_font,
                    fontSize=16,
                    spaceAfter=10
                )))
                elements.append(Spacer(1, 0.3*cm))

                # 短语：一行2个
                phrase_table_data = []
                for i in range(0, len(phrase_items), 2):
                    row = []
                    for j in range(2):
                        if i + j < len(phrase_items):
                            word = phrase_items[i + j]
                            item = DictationItem(word['chinese'], width=8*cm, chinese_font=self.chinese_font)
                            row.append(item)
                        else:
                            row.append('')
                    phrase_table_data.append(row)

                phrase_table = Table(phrase_table_data, colWidths=[8*cm, 8*cm])
                phrase_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(phrase_table)
                elements.append(Spacer(1, 0.8*cm))

            if sentence_items:
                elements.append(Paragraph('三、句子', ParagraphStyle(
                    'SectionTitle',
                    fontName=self.chinese_font,
                    fontSize=16,
                    spaceAfter=10
                )))
                elements.append(Spacer(1, 0.3*cm))

                # 句子：一行1个
                sentence_table_data = []
                for word in sentence_items:
                    item = DictationItem(word['chinese'], width=16*cm, chinese_font=self.chinese_font)
                    sentence_table_data.append([item])

                sentence_table = Table(sentence_table_data, colWidths=[16*cm])
                sentence_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(sentence_table)

        return elements

    def _create_answer_page(self, words: List[Dict], unit_name: str) -> List:
        """创建答案页"""
        elements = []

        # 标题样式
        title_style = ParagraphStyle(
            'Title',
            parent=getSampleStyleSheet()['Title'],
            fontName=self.chinese_font,
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=20
        )

        # 标题
        title = Paragraph(f'英语单词默写答案 - {unit_name}', title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))

        # 中英文样式
        chinese_style = ParagraphStyle(
            'Chinese',
            fontName=self.chinese_font,
            fontSize=10,
            alignment=TA_CENTER
        )

        english_style = ParagraphStyle(
            'English',
            fontName='Helvetica',
            fontSize=12,
            alignment=TA_CENTER
        )

        # 按类型分组单词
        word_items = [w for w in words if w['type'] == '单词']
        non_word_items = [w for w in words if w['type'] != '单词']

        # 添加单词部分
        if word_items:
            elements.append(Paragraph('一、单词', ParagraphStyle(
                'SectionTitle',
                fontName=self.chinese_font,
                fontSize=16,
                spaceAfter=10
            )))
            elements.append(Spacer(1, 0.3*cm))

            # 单词：一行4个
            word_table_data = []
            for i in range(0, len(word_items), 4):
                row = []
                for j in range(4):
                    if i + j < len(word_items):
                        word = word_items[i + j]
                        # 创建一个包含中文和英文的单元格
                        cell_content = [
                            Paragraph(word['chinese'], chinese_style),
                            Paragraph(word['english'], english_style)
                        ]
                        row.append(cell_content)
                    else:
                        row.append('')
                word_table_data.append(row)

            word_table = Table(word_table_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
            word_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(word_table)
            elements.append(Spacer(1, 0.8*cm))

        # 添加短语和句子部分
        if non_word_items:
            # 按类型分组
            phrase_items = [w for w in non_word_items if w['type'] == '短语']
            sentence_items = [w for w in non_word_items if w['type'] == '句子']

            if phrase_items:
                elements.append(Paragraph('二、短语', ParagraphStyle(
                    'SectionTitle',
                    fontName=self.chinese_font,
                    fontSize=16,
                    spaceAfter=10
                )))
                elements.append(Spacer(1, 0.3*cm))

                # 短语：一行2个
                phrase_table_data = []
                for i in range(0, len(phrase_items), 2):
                    row = []
                    for j in range(2):
                        if i + j < len(phrase_items):
                            word = phrase_items[i + j]
                            cell_content = [
                                Paragraph(word['chinese'], chinese_style),
                                Paragraph(word['english'], english_style)
                            ]
                            row.append(cell_content)
                        else:
                            row.append('')
                    phrase_table_data.append(row)

                phrase_table = Table(phrase_table_data, colWidths=[8*cm, 8*cm])
                phrase_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(phrase_table)
                elements.append(Spacer(1, 0.8*cm))

            if sentence_items:
                elements.append(Paragraph('三、句子', ParagraphStyle(
                    'SectionTitle',
                    fontName=self.chinese_font,
                    fontSize=16,
                    spaceAfter=10
                )))
                elements.append(Spacer(1, 0.3*cm))

                # 句子：一行1个
                sentence_table_data = []
                for word in sentence_items:
                    cell_content = [
                        Paragraph(word['chinese'], chinese_style),
                        Paragraph(word['english'], english_style)
                    ]
                    sentence_table_data.append([cell_content])

                sentence_table = Table(sentence_table_data, colWidths=[16*cm])
                sentence_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(sentence_table)

        return elements