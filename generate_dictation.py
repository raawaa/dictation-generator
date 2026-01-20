#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英语单词默写纸生成器
从CSV文件中抽取单词，生成PDF格式的默写纸
"""

import csv
import random
import argparse
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from __version__ import __version__, __author__, __description__
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

    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.vocabulary = []
        self.unit_dict = {}

        # 注册中文字体
        self._register_fonts()

    def _register_fonts(self):
        """注册中文字体"""
        # 尝试使用系统自带的中文字体
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',  # macOS
            '/System/Library/Fonts/STHeiti Light.ttc',  # macOS
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Linux
            'C:/Windows/Fonts/msyh.ttc',  # Windows
        ]

        self.chinese_font = 'Helvetica'
        for font_path in font_paths:
            if Path(font_path).exists():
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    self.chinese_font = 'ChineseFont'
                    break
                except:
                    continue

    def load_vocabulary(self):
        """从CSV文件加载词汇数据"""
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

    def get_words_by_units(self, units, count=None, word_type=None):
        """根据单元获取单词

        Args:
            units: 单元列表，如 ['M1', 'M2']
            count: 需要抽取的单词数量
            word_type: 单词类型，如 '单词', '短语', '句子'

        Returns:
            抽取的单词列表
        """
        words = []
        for unit in units:
            if unit in self.unit_dict:
                unit_words = self.unit_dict[unit]
                if word_type:
                    if isinstance(word_type, list):
                        unit_words = [w for w in unit_words if w['type'] in word_type]
                    else:
                        unit_words = [w for w in unit_words if w['type'] == word_type]
                words.extend(unit_words)

        if count is not None and len(words) > count:
            words = random.sample(words, count)

        return words

    def generate_pdf(self, words, output_file, unit_name='M1'):
        """生成PDF默写纸

        Args:
            words: 单词列表
            output_file: 输出文件路径
            unit_name: 单元名称
        """
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

    def _create_dictation_page(self, words, unit_name):
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

    def _create_answer_page(self, words, unit_name):
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


def main():
    parser = argparse.ArgumentParser(description='英语单词默写纸生成器')
    parser.add_argument('--csv', type=str, default='data/校内英语单词.csv',
                        help='CSV文件路径（默认：data/校内英语单词.csv）')
    parser.add_argument('--unit', type=str, default='M1',
                        help='单元名称，如 M1, M2（默认：M1）')
    parser.add_argument('--units', type=str,
                        help='多个单元，用逗号分隔，如 M1,M2,M3')
    parser.add_argument('--count', type=int, default=None,
                        help='抽取的单词数量（不指定则生成全部）')
    parser.add_argument('--copies', type=int, default=1,
                        help='生成的份数（默认：1）')
    parser.add_argument('--type', type=str,
                        help='单词类型，可用逗号分隔多个类型（默认：全部）')
    parser.add_argument('--output-dir', type=str, default='.',
                        help='输出目录（默认：当前目录）')
    parser.add_argument('--version', action='version',
                        version=f'{__description__} {__version__}')

    args = parser.parse_args()

    # 创建生成器
    generator = DictationGenerator(args.csv)
    generator.load_vocabulary()

    # 确定单元列表
    if args.units:
        units = [u.strip() for u in args.units.split(',')]
    else:
        units = [args.unit]

    # 确定类型列表
    word_types = None
    if args.type:
        word_types = [t.strip() for t in args.type.split(',')]

    # 生成多份默写纸
    for copy_num in range(1, args.copies + 1):
        # 随机抽取单词
        words = generator.get_words_by_units(units, args.count, word_types)

        if not words:
            print(f'警告：没有找到符合条件的单词（单元：{units}，类型：{args.type}）')
            continue

        # 生成文件名
        unit_str = '_'.join(units)
        date_str = datetime.now().strftime('%Y%m%d')
        output_file = str(Path(args.output_dir) / f'默写纸_{unit_str}_{date_str}_{copy_num:02d}.pdf')

        # 生成PDF
        generator.generate_pdf(words, output_file, unit_str)
        print(f'已生成：{output_file}')


if __name__ == '__main__':
    main()