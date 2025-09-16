# 血液疾病临床预测分析系统

**版本**: 3.0.0 (重构版)  
**语言**: Python 3.8+  
**领域**: 临床数据分析和可视化

## 项目概述

这是一个专为血液疾病临床预测而设计的数据分析和可视化系统。系统采用模块化架构，支持分类变量的自动分析、分组可视化和综合报告生成。

### 主要特性

- 🔍 **自动分类变量分析**: 智能识别和分析分类变量
- 📊 **分组可视化**: 将变量按组（每组5个）进行可视化
- 🎨 **可配置图表**: 支持自定义颜色、尺寸和布局
- 📋 **综合报告**: 自动生成分析报告和数据表
- ⚙️ **灵活配置**: YAML配置文件和命令行参数支持
- 🏗️ **模块化架构**: 清晰的代码组织和易于维护

## 系统架构

```
dataset_clip/
├── main.py                 # 主程序入口和工作流协调
├── config_manager.py       # 配置管理和验证
├── data_analyzer.py        # 数据分析核心逻辑  
├── data_visualizer.py      # 数据可视化和图表生成
├── config.yaml             # 系统配置文件
├── README.md               # 项目文档（本文件）
└── output/                 # 输出目录
    ├── analysis_report.txt
    ├── grouped_visualization.png
    └── data_table.csv
```

### 模块说明

| 模块 | 职责 | 主要功能 |
|------|------|----------|
| `main.py` | 工作流协调 | 参数解析、配置加载、流程控制 |
| `config_manager.py` | 配置管理 | YAML加载、验证、默认值处理 |
| `data_analyzer.py` | 数据分析 | 分类变量识别、统计分析、报告生成 |
| `data_visualizer.py` | 数据可视化 | 分组图表、布局优化、样式配置 |
工作流: main → config → analyzer → visualizer
#### 数据流和处理逻辑：
输入数据 → 配置加载 → 数据分析 → 报告生成 → 可视化创建 → 输出文件

## 快速开始

### 1. 环境准备

```bash
# 安装依赖包
pip install pandas numpy matplotlib seaborn pyyaml

# 确保数据文件就位
ls /path/to/your/encoded_standardized.csv
```

### 2. 基本使用

```bash
# 使用默认配置运行
python main.py

# 指定输入文件和输出目录
python main.py --input-file /path/to/data.csv --output-dir ./results

# 使用自定义配置
python main.py --config config.yaml
```

### 3. 检查输出

```bash
ls output/
# analysis_report.txt      - 详细分析报告
# grouped_visualization.png - 分组可视化图表
# data_table.csv          - 分析数据表
```

## 配置说明

### 配置优先级

系统按以下优先级顺序加载配置（从高到低）：

1. **命令行参数**（最高优先级）
2. **YAML配置文件**
3. **环境变量**
4. **默认值**（最低优先级）

### 配置文件结构 (`config.yaml`)

```yaml
# 数据路径配置
data_processing:
  input_file: "/path/to/encoded_standardized.csv"
  output_dir: "./output"
  backup_input_file: "/path/to/backup.csv"  # 备用数据文件
  
# 数据分析参数  
analysis:
  age_threshold: 65
  exclude_columns:
    - "ID"
    - "Timestamp"
    
# 可视化配置
visualization:
  figure_width: 25
  figure_height: 8
  dpi: 300
  spacing: 4.0
  
  # 布局边距设置
  top_margin: 0.92
  bottom_margin: 0.08
  left_margin: 0.08
  right_margin: 0.95
  wspace: 0.3  # 子图水平间距
  hspace: 0.4  # 子图垂直间距
  
  # 颜色配置
  colors:
    - "#FF6B6B"  # 珊瑚红
    - "#4ECDC4"  # 青绿色
    - "#45B7D1"  # 天蓝色
    - "#96CEB4"  # 薄荷绿
    - "#FECA57"  # 柠檬黄
    
  # 样式设置
  alpha: 0.8
  grid_alpha: 0.3
  bar_width: 0.6
  category_spacing: 0.1
  variable_spacing: 0.2

# 显示配置
display:
  fonts:
    - "Microsoft YaHei"  # 中文字体
    - "SimHei"
    - "DejaVu Sans"
    - "Arial Unicode MS"
    
  font_sizes:
    title: 16
    subtitle: 14
    axis: 12
    tick: 10

# 输出文件配置
output:
  report_filename: "analysis_report.txt"
  visualization_filename: "grouped_visualization.png"
  data_filename: "data_table.csv"
  encoding: "utf-8"
```

### 配置部分详解

#### 路径部分 (data_processing)
- `input_file`: 主要CSV数据文件路径
- `output_dir`: 生成的报告和可视化的目录
- `backup_input_file`: 如果主文件未找到的备用文件路径

#### 分析部分 (analysis)
- `age_threshold`: 患者分组的年龄截止点（年）
- `exclude_columns`: 从分析中排除的列名列表

#### 可视化部分 (visualization)
- `figure_width/height`: 图表尺寸（英寸）
- `dpi`: 图像分辨率（默认：300）
- `colors`: 图表元素的颜色调色板
- `alpha`: 条形透明度（0.0-1.0）
- `grid_alpha`: 网格线透明度
- `bar_width`: 单个条形宽度
- `category_spacing`: 类别间距
- `variable_spacing`: 变量组间距
- 边距设置: `top_margin`, `bottom_margin`, `left_margin`, `right_margin`
- 间距设置: `wspace`（水平）, `hspace`（垂直）

#### 显示部分 (display)
- `fonts`: 字体偏好列表（按优先级排序）
- `font_sizes`: 不同文本元素的字体大小映射

#### 输出部分 (output)
- `report_filename`: 文本报告文件名
- `visualization_filename`: 图表图像文件名
- `data_filename`: 数据表CSV文件名
- `encoding`: 输出文件的文本编码

### 命令行参数

| 参数 | 简写 | 类型 | 说明 | 示例 |
|------|------|------|------|------|
| `--config` | `-c` | 路径 | 配置文件路径 | `-c config.yaml` |
| `--input-file` | `-i` | 路径 | 输入CSV文件 | `-i data.csv` |
| `--output-dir` | `-o` | 路径 | 输出目录 | `-o ./results` |
| `--age-threshold` | `-a` | 整数 | 年龄分组阈值（默认：65） | `-a 70` |
| `--figure-width` | | 浮点 | 图表宽度（英寸，默认：25） | `--figure-width 30` |
| `--figure-height` | | 浮点 | 图表高度（英寸，默认：8） | `--figure-height 10` |
| `--dpi` | | 整数 | 图形DPI（默认：300） | `--dpi 150` |
| `--version` | `-v` | | 显示版本并退出 | `-v` |
| `--help` | `-h` | | 显示帮助信息并退出 | `-h` |

### 环境变量配置

设置这些环境变量来配置系统：

| 变量名 | 类型 | 描述 | 示例 |
|--------|------|------|------|
| `CLIP_CONFIG_FILE` | 字符串 | YAML配置文件路径 | `export CLIP_CONFIG_FILE="config.yaml"` |
| `CLIP_INPUT_FILE` | 字符串 | 输入CSV文件路径 | `export CLIP_INPUT_FILE="data.csv"` |
| `CLIP_OUTPUT_DIR` | 字符串 | 输出目录路径 | `export CLIP_OUTPUT_DIR="./output"` |
| `CLIP_AGE_THRESHOLD` | 整数 | 年龄分组阈值 | `export CLIP_AGE_THRESHOLD=70` |
| `CLIP_FIGURE_WIDTH` | 浮点数 | 图形宽度（英寸） | `export CLIP_FIGURE_WIDTH=30` |
| `CLIP_FIGURE_HEIGHT` | 浮点数 | 图形高度（英寸） | `export CLIP_FIGURE_HEIGHT=10` |
| `CLIP_DPI` | 整数 | 图形DPI | `export CLIP_DPI=150` |

#### 环境变量设置示例
```bash
export CLIP_INPUT_FILE="/home/user/data/my_data.csv"
export CLIP_OUTPUT_DIR="/home/user/output"
export CLIP_AGE_THRESHOLD=70
python main.py
```

## 使用场景

### 场景1: 标准临床数据分析

```bash
# 使用默认配置分析标准格式的临床数据
python main.py --input-file clinical_data.csv
```

**输出**:
- 分类变量自动识别和统计
- 按年龄组(≥65岁, <65岁)分层分析
- 每组5个变量的可视化图表

### 场景2: 自定义年龄分组

```bash
# 将年龄分组阈值改为70岁
python main.py --input-file clinical_data.csv --age-threshold 70
```

### 场景3: 高分辨率图表生成

```bash
# 生成高分辨率、大尺寸图表用于报告
python main.py \
  --input-file clinical_data.csv \
  --figure-width 30 \
  --figure-height 12 \
  --output-dir ./high_res_output
```

### 场景4: 批量处理配置

```yaml
# batch_config.yaml
data_processing:
  input_file: "batch_data.csv"
  output_dir: "./batch_results"

analysis:
  age_threshold: 60

visualization:
  figure_width: 35
  figure_height: 15
  dpi: 300
```

```bash
python main.py --config batch_config.yaml
```

### 场景5: 组合配置方法

```bash
# 使用配置文件作为基础，然后覆盖特定值
python main.py --config config.yaml --age-threshold 75 --dpi 150

# 使用环境变量 + 命令行参数组合
export CLIP_INPUT_FILE="/data/clinical.csv"
export CLIP_OUTPUT_DIR="/results"
python main.py --age-threshold 70 --figure-width 20 --figure-height 14
```

## 输出详解

### 1. 分析报告 (`analysis_report.txt`)

```
血液疾病临床预测 - 分类变量分析报告
===========================================

数据集概述:
- 总样本数: 1,250
- 分类变量数: 18
- 年龄分组阈值: 65岁

年龄组分布:
- ≥65岁: 723人 (57.8%)
- <65岁: 527人 (42.2%)

分类变量分析:
...
```

### 2. 可视化图表 (`grouped_visualization.png`)

- **分组布局**: 每组最多5个变量
- **图表类型**: 堆叠条形图
- **年龄分层**: 不同颜色表示不同年龄组
- **高分辨率**: 300 DPI，适合报告使用

### 3. 数据表 (`data_table.csv`)

包含所有分析结果的结构化数据，便于进一步处理和统计。

## 高级配置

### 自定义颜色主题

```yaml
visualization:
  colors:
    - "#E74C3C"  # 红色主题
    - "#3498DB"  # 蓝色主题
    - "#2ECC71"  # 绿色主题
    - "#F39C12"  # 橙色主题
    - "#9B59B6"  # 紫色主题
```

### 布局微调

```yaml
visualization:
  # 精确控制图表布局
  top_margin: 0.95    # 顶部留白
  bottom_margin: 0.05 # 底部留白
  left_margin: 0.06   # 左侧留白
  right_margin: 0.98  # 右侧留白
  wspace: 0.25        # 子图水平间距
  hspace: 0.35        # 子图垂直间距
```

### 字体和样式

```yaml
display:
  fonts:
    - "Microsoft YaHei"  # 中文字体
    - "Arial Unicode MS"
    - "DejaVu Sans"
    
  font_sizes:
    title: 16
    subtitle: 14
    axis: 12
    tick: 10
```







## 技术规格

- **Python版本**: 3.8+
- **核心依赖**: pandas, numpy, matplotlib, seaborn, PyYAML
- **内存需求**: 最小2GB（取决于数据大小）
- **输出格式**: PNG（图表）、TXT（报告）、CSV（数据）

## 更新日志

### v3.0.0 (当前版本) - 2024年12月
- ✅ 完全重构为模块化架构
- ✅ 改进的可视化布局和间距控制
- ✅ 增强的配置管理系统（支持优先级配置）
- ✅ 优化的错误处理机制
- ✅ 完善的文档和使用指南
- ✅ 新增环境变量配置支持
- ✅ 增强的命令行参数处理

### v2.0.0 (模块化重构版)
- 引入模块化设计和配置优先级系统
- 添加配置管理器和环境变量支持
- 改进命令行界面和参数处理
- 增强错误处理和文件备用机制
- 保持向后兼容性

### v1.0.0 (初始版本)
- 初始单体版本实现
- 基本分析和可视化功能
- 简单配置文件支持

