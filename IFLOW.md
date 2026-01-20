# 英语单词默写纸生成器

## 项目概述

这是一个Python项目，用于从CSV文件中抽取英语单词、短语和句子，生成PDF格式的默写纸。该项目专门为小学生英语学习设计，生成的默写纸采用标准的英文练习本样式，包含四线格（其中中间线为红色虚线），便于学生规范书写。

### 主要功能

- 从CSV文件读取词汇数据（包含中文、英文、单元、年级、类别等信息）
- 支持按单元筛选词汇（如M1、M2、M3等）
- 支持按类型筛选（单词、短语、句子）
- 随机抽取指定数量的词汇
- 生成PDF格式的默写纸，包含默写页和答案页
- 支持生成多份不同的默写纸（每次随机抽取）

### 技术栈

- **语言**: Python 3.12+
- **PDF生成**: ReportLab 4.4+
- **数据处理**: csv, random, argparse

### 项目结构

```
school-vocabulary/
├── generate_dictation.py    # 主程序：默写纸生成器
├── 校内英语单词.csv          # 词汇数据文件
└── IFLOW.md                  # 项目说明文档
```

## 构建和运行

### 环境准备

1. 确保已安装Python 3.12+
2. 安装依赖项：

```bash
pip3 install reportlab
```

### 运行方式

```bash
python3 generate_dictation.py [选项]
```

### 常用命令

**生成M1单元的默写纸，15个单词，1份**
```bash
python3 generate_dictation.py --unit M1 --count 15
```

**生成多个单元的默写纸，20个单词，2份**
```bash
python3 generate_dictation.py --units M1,M2,M3 --count 20 --copies 2
```

**只生成单词类型的默写纸**
```bash
python3 generate_dictation.py --unit M1 --count 10 --type 单词
```

**只生成短语类型的默写纸**
```bash
python3 generate_dictation.py --unit M1 --count 10 --type 短语
```

**只生成句子类型的默写纸**
```bash
python3 generate_dictation.py --unit M1 --count 10 --type 句子
```

**查看帮助信息**
```bash
python3 generate_dictation.py --help
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--csv` | CSV文件路径 | `校内英语单词.csv` |
| `--unit` | 单元名称（单个） | `M1` |
| `--units` | 多个单元（逗号分隔） | 无 |
| `--count` | 抽取的单词数量 | `15` |
| `--copies` | 生成的份数 | `1` |
| `--type` | 单词类型（单词/短语/句子） | 全部 |
| `--output-dir` | 输出目录 | 当前目录 |

## 数据格式

`校内英语单词.csv` 文件格式：

```csv
中文,英文,单元,年级,类别
遇到,meet,M1,四年级上半学期,单词
人们,people,M1,四年级上半学期,单词
展示一张你朋友的照片,show a photo of your friend,M1,四年级上半学期,短语
她的姓名是莎莉。,Her name is Sally.,M1,四年级上半学期,句子
```

**字段说明：**
- `中文`: 中文翻译
- `英文`: 英文单词/短语/句子
- `单元`: 单元编号（如M1、M2、M3、M4）
- `年级`: 年级信息
- `类别`: 类型（单词、短语、句子）

## 输出格式

生成的PDF文件命名格式：`默写纸_{单元}_{日期}_{序号}.pdf`

例如：`默写纸_M1_M2_M3_20260118_01.pdf`

### PDF布局

**默写页：**
- 标题：英语单词默写 - {单元名称}
- 信息行：日期、姓名、分数
- 按类型分组显示：
  - **单词**：一行4个，每个包含四线格（上）+ 中文（下）
  - **短语**：一行2个，每个包含四线格（上）+ 中文（下）
  - **句子**：一行1个，包含四线格（上）+ 中文（下）

**答案页：**
- 标题：英语单词默写答案 - {单元名称}
- 按类型分组显示答案，格式与默写页一致

### 四线格样式

标准英文练习本样式，从上到下：
1. 黑色实线
2. 黑色实线
3. 红色虚线（中间线）
4. 黑色实线

线间距：0.3cm，适合小学生书写

## 开发约定

### 代码风格

- 使用Python 3类型提示（如适用）
- 遵循PEP 8代码风格
- 使用中文注释和文档字符串
- 函数和类使用描述性名称

### 主要类说明

- `DictationGenerator`: 主生成器类，负责读取数据、生成PDF
- `FourLineGrid`: 自定义Flowable类，绘制四线格
- `DictationItem`: 自定义Flowable类，封装单个默写项（四线格+中文）

### 扩展指南

如需修改布局或样式，主要关注以下方法：
- `_create_dictation_page()`: 创建默写页
- `_create_answer_page()`: 创建答案页
- `FourLineGrid.draw()`: 绘制四线格
- `DictationItem.draw()`: 绘制单个默写项

## 注意事项

- 中文显示依赖系统字体，脚本会自动尝试使用系统自带的中文字体（如PingFang、STHeiti等）
- 生成的PDF文件为A4纸张大小
- 每次运行会生成新的PDF文件，文件名包含日期和时间戳
- CSV文件编码必须为UTF-8