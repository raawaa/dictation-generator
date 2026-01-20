# 英语单词默写纸生成器

从 CSV 文件中抽取英语单词、短语和句子，生成 PDF 格式的默写纸。专为小学生英语学习设计，采用标准的英文练习本样式（四线格）。

## 功能特点

- 从 CSV 文件读取词汇数据
- 支持按单元筛选词汇（如 M1、M2、M3 等）
- 支持按类型筛选（单词、短语、句子）
- 随机抽取指定数量的词汇，或不指定数量则生成全部
- 生成 PDF 格式的默写纸，包含默写页和答案页
- 支持生成多份不同的默写纸（每次随机抽取）

## 环境要求

- Python 3.12+

## 安装依赖

```bash
pip3 install reportlab
```

## 使用方法

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--csv` | CSV 文件路径 | `校内英语单词.csv` |
| `--unit` | 单元名称（单个） | `M1` |
| `--units` | 多个单元（逗号分隔） | 无 |
| `--count` | 抽取的单词数量 | `None`（生成全部） |
| `--copies` | 生成的份数 | `1` |
| `--type` | 单词类型（单词/短语/句子） | 全部 |
| `--output-dir` | 输出目录 | 当前目录 |

### 使用示例

**生成 M2 单元的全部词汇**
```bash
python3 generate_dictation.py --unit M2
```

**生成 M1 单元的 20 个随机词汇**
```bash
python3 generate_dictation.py --unit M1 --count 20
```

**生成多个单元的默写纸（M1、M2、M3）**
```bash
python3 generate_dictation.py --units M1,M2,M3
```

**只生成单词类型的默写纸**
```bash
python3 generate_dictation.py --unit M1 --type 单词
```

**只生成短语类型的默写纸**
```bash
python3 generate_dictation.py --unit M1 --type 短语
```

**只生成句子类型的默写纸**
```bash
python3 generate_dictation.py --unit M1 --type 句子
```

**生成 3 份不同的默写纸**
```bash
python3 generate_dictation.py --unit M2 --count 15 --copies 3
```

**指定输出目录**
```bash
python3 generate_dictation.py --unit M2 --output-dir ./output
```

**使用自定义 CSV 文件**
```bash
python3 generate_dictation.py --csv my_vocabulary.csv --unit M1
```

**查看帮助信息**
```bash
python3 generate_dictation.py --help
```

## 数据格式

CSV 文件必须包含以下字段：

```csv
中文,英文,单元,年级,类别
遇到,meet,M1,四年级上半学期,单词
人们,people,M1,四年级上半学期,单词
展示一张你朋友的照片,show a photo of your friend,M1,四年级上半学期,短语
她的姓名是莎莉。,Her name is Sally.,M1,四年级上半学期,句子
```

**字段说明：**
- `中文`：中文翻译
- `英文`：英文单词/短语/句子
- `单元`：单元编号（如 M1、M2、M3、M4）
- `年级`：年级信息
- `类别`：类型（单词、短语、句子）

**注意事项：**
- CSV 文件编码必须为 UTF-8
- 第一行为表头

## 输出格式

生成的 PDF 文件命名格式：`默写纸_{单元}_{日期}_{序号}.pdf`

例如：`默写纸_M2_20260118_01.pdf`

### PDF 布局

**默写页（第 1 页）：**
- 标题：英语单词默写 - {单元名称}
- 信息行：日期、姓名、分数
- 按类型分组显示：
  - **一、单词**：一行 4 个，每个包含四线格（上）+ 中文（下）
  - **二、短语**：一行 2 个，每个包含四线格（上）+ 中文（下）
  - **三、句子**：一行 1 个，包含四线格（上）+ 中文（下）

**答案页（第 2 页）：**
- 标题：英语单词默写答案 - {单元名称}
- 按类型分组显示答案，格式与默写页一致

### 四线格样式

标准英文练习本样式，从上到下：
1. 黑色实线
2. 黑色实线
3. 红色虚线（中间线）
4. 黑色实线

线间距：0.3cm，适合小学生书写

## 技术栈

- **语言**：Python 3.12+
- **PDF 生成**：ReportLab 4.4+
- **数据处理**：csv, random, argparse