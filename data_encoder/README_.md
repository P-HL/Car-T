# CAR-T 治疗临床数据处理系统


> 专业的CAR-T细胞治疗临床数据处理系统，支持数据验证、处理和标准化的完整工作流程。

## 📋 目录

- [系统概述](#系统概述)
- [项目结构](#项目结构)
- [数据格式转换工具](#数据格式转换工具)
- [安装指南](#安装指南)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
- [配置管理](#配置管理)
- [主要功能](#主要功能)
- [数据处理流程](#数据处理流程)
- [故障排除](#故障排除)
- [输入/输出格式](#输入输出格式)
- [开发和扩展](#开发和扩展)

## 🎯 系统概述

CAR-T 数据处理系统是一个模块化的Python应用程序，专门设计用于处理CAR-T细胞治疗的临床数据。系统采用现代化的配置管理、步骤控制和报告生成机制，确保数据处理的准确性和可追溯性。

**⚡ 最新更新**: 项目已完成模块化重构，将工具函数组织到 `utils/` 目录中，配置变量采用统一的 `static_` 和 `dynamic_` 前缀命名约定，提高了代码的可维护性和可读性。

### 核心特性

- **🔍 智能数据验证**: 全面的数据质量检查和结构验证
- **⚙️ 灵活数据处理**: 可配置的列删除、重命名和清理功能
- **📊 详细报告生成**: 完整的验证和处理报告
- **🎛️ 多模式支持**: 动态时间序列和静态数据处理
- **🔧 模块化架构**: 易于扩展和维护的代码结构
- **📝 集中配置管理**: 支持YAML配置、环境变量和命令行参数
- **🛠️ 工具模块化**: 核心工具函数集中在 `utils/` 目录中

## 📁 项目结构

### 完整文件结构概览

```
/home/phl/PHL/Car-T/data_encoder/
├── 🚀 主程序文件
│   └── data_processed.py              # 主入口文件和工作流程协调器
│
├── 🛠️ 工具模块 (utils/)
│   ├── __init__.py                    # 模块初始化文件
│   ├── config_manager.py              # 配置管理核心模块
│   ├── cli_parser.py                  # 命令行参数解析器
│   └── format_xlsx_to_csv.py          # Excel转CSV格式转换工具
│
├── 📦 动态数据处理模块 (dynamic_data_processing/)
│   ├── __init__.py                    # 模块初始化文件
│   ├── validator.py                   # 数据验证器 - 文件结构和数据质量检查
│   ├── processor.py                   # 数据处理器 - 列操作和数据清理
│   └── step_executor.py               # 步骤执行器 - 工作流程控制
│
├── 🔧 静态数据处理模块 (static_data_processing/)
│   ├── __init__.py                    # 模块初始化文件
│   ├── static_validator.py            # 静态数据验证器
│   ├── static_processor.py            # 静态数据处理器
│   └── static_converters.py           # 数据转换函数集
│
├── ⚙️ 配置文件
│   ├── config.yaml                    # 主配置文件（重新组织结构）
│   └── config_sample.yaml             # 示例配置文件模板
│
├── 📄 文档
│   ├── README.md                      # 项目文档（本文件）
│   └── READMEa.md                     # 参考文档
│
└── 📂 输出目录
    └── output/                        # 处理后数据的输出目录
```

## 🔧 数据格式转换工具

### format_xlsx_to_csv.py

**简要说明：**
此工具位于 `utils/` 目录中，负责将 Excel (.xlsx) 文件批量转换为 CSV 格式，作为数据处理流程的预处理步骤。由于后续的数据分析和处理工作流程主要基于 CSV 格式，此转换工具确保了数据格式的统一性和兼容性。

**功能特性：**
- 批量处理多个 Excel 文件
- 自动创建输出目录
- 保持原始文件名结构
- 错误处理和进度提示

**使用说明：**


```bash
# 支持的文件格式
- **输入格式：** .xlsx (Excel 工作簿)
- **输出格式：** .csv (逗号分隔值文件)

# 参数说明
- `input_folder` (str): 包含 .xlsx 文件的输入目录路径
- `output_folder` (str): CSV 文件的输出目录路径（自动创建）

# 示例用法
input_folder = "/data/raw_excel_files/"
output_folder = "/data/processed_csv/"
```

#### 命令行使用
```bash
# 直接运行脚本
cd /home/phl/PHL/Car-T/data_encoder
python utils/format_xlsx_to_csv.py
```


**数据处理流程中的位置：**
```
原始数据 (.xlsx) → [utils/format_xlsx_to_csv.py] → CSV 文件 → 后续 EDA 分析 → 建模
```

此转换工具作为整个 CAR-T 数据处理流程的第一步，确保所有输入数据都是统一的 CSV 格式，为后续的探索性数据分析 (EDA) 和机器学习建模提供标准化的数据输入。

**注意事项：**
- 确保输入目录中包含有效的 .xlsx 文件
- 输出目录会自动创建，无需手动创建
- 转换过程中如遇到损坏的文件，会跳过并显示错误信息
- 转换后的 CSV 文件使用 UTF-8 编码

## 🚀 安装指南

### 系统要求

- **Python**: 3.8 或更高版本
- **操作系统**: Linux, macOS, Windows
- **内存**: 建议 4GB 或更多（用于大数据集处理）

### 依赖项安装

```bash
# 安装核心依赖
pip install pandas>=1.3.0 numpy>=1.21.0 pyyaml>=5.4.0
```

### 环境设置

1. **进入项目目录**:
   ```bash
   cd /home/phl/PHL/Car-T/data_encoder
   ```

2. **验证安装**:
   ```bash
   python data_processed.py --help
   ```

3. **创建输出目录**（如果不存在）:
   ```bash
   mkdir -p output
   ```

## ⚡ 快速开始

### 5分钟入门示例

```bash
# 步骤1: 创建示例配置文件
python data_processed.py --create-sample-config

# 步骤2: 查看当前配置
python data_processed.py --print-config

# 步骤3: 运行数据格式转换工具（推荐的第一步）
python utils/format_xlsx_to_csv.py

# 步骤4: 运行动态/静态数据验证（运行之前先配置好config中的相关参数）
python data_processed.py --mode dynamic/static --config config.yaml --validation-only

# 步骤5: 如果验证通过，运行完整数据处理
# 静态数据标准化编码
# 动态数据删除冗余项指标，其中删除拷贝数和淋巴亚群相关指标为可选项
# （命令行使用--enable-column-deletion，config中配置remove_optional_columns为true）
python data_processed.py --mode dynamic/static --config config.yaml --processing-only
```

### 基本使用流程

```bash
# 1. 默认模式 - 仅进行数据验证
python data_processed.py --mode dynamic

# 2. 查看帮助信息
python data_processed.py --help

# 3. 指定输入输出目录
python data_processed.py --mode dynamic --input-dir /path/to/data --output-dir /path/to/results

# 4. 使用配置文件运行
python data_processed.py --mode dynamic --config config.yaml
```

## 🔧 使用方法

### 动态数据处理（默认模式）

**注意: --mode 参数现在是必需的，必须明确指定处理模式。**

```bash
# 基本动态数据处理(默认只进行数据验证)
python data_processed.py --mode dynamic

# 只进行数据验证
python data_processed.py --mode dynamic --validation-only

# 只进行数据处理
python data_processed.py --mode dynamic --processing-only

# 使用配置文件
python data_processed.py --mode dynamic --config config.yaml

# 指定输入输出目录
python data_processed.py --mode dynamic --input-dir /path/to/input --output-dir /path/to/output

# 启用列删除功能
python data_processed.py --mode dynamic --enable-column-deletion

# 跳过交互式询问
python data_processed.py --mode dynamic --skip-interactive --enable-column-deletion
```

### 静态数据处理模式

静态数据处理的输入和输出文件通过配置文件指定。

```bash
# 基本静态数据处理（需要配置文件）
python data_processed.py --mode static --config config.yaml （可选，默认为验证模式：--validation-only/--processing-only）

# 使用自定义配置文件
python data_processed.py --mode static --config my_config.yaml
```

配置文件中的静态处理配置：
```yaml
# 静态数据处理配置
static_input_file: /home/phl/PHL/Car-T/datasetcart/encoded.csv
static_output_file: /home/phl/PHL/Car-T/data_encoder/output/dataset/encoded_standardized.csv
static_expected_column_count: 22
static_expected_patient_count: 500
static_validation_only: true
static_processing_only: false
```

### 实用功能

```bash
# 创建示例配置文件
python data_processed.py --create-sample-config

# 显示当前配置
python data_processed.py --print-config

# 显示帮助信息
python data_processed.py --help
```

## ⚙️ 配置管理

系统支持多层配置，按优先级排序：
1. 命令行参数（最高优先级）
2. YAML配置文件
3. 环境变量（最低优先级）

### 环境变量

```bash
# 基本路径配置
export CART_INPUT_DIR="/path/to/input"
export CART_OUTPUT_DIR="/path/to/output"

# 静态数据处理配置
export CART_STATIC_INPUT_FILE="/path/to/patient_info.csv"
export CART_STATIC_OUTPUT_FILE="/path/to/processed_static_data.csv"

# 动态数据验证参数
export CART_DYNAMIC_EXPECTED_FILE_COUNT=500
export CART_DYNAMIC_EXPECTED_ROW_COUNT=46

# 动态数据步骤控制
export CART_DYNAMIC_VALIDATION_ONLY=true
export CART_DYNAMIC_PROCESSING_ONLY=false

# 处理控制
export CART_ENABLE_COLUMN_DELETION=false
export CART_VERBOSE=true
```

### YAML配置文件结构

```yaml
# 静态数据配置部分
static_input_file: /home/phl/PHL/Car-T/datasetcart/patient_info.csv
static_output_file: /home/phl/PHL/Car-T/data_encoder/output/processed_static_data.csv
static_expected_column_count: 22
static_expected_patient_count: 500
static_validation_only: true
static_processing_only: false

# 动态数据配置部分
input_dir: /home/phl/PHL/Car-T/datasetcart/processed
output_dir: /home/phl/PHL/Car-T/data_encoder/output

# 动态数据验证配置
dynamic_expected_file_count: 500
dynamic_expected_row_count: 46
dynamic_expected_time_range_start: -15
dynamic_expected_time_range_end: 30

# 列删除配置
enable_column_deletion: false
cbc_columns_to_delete: [2, 4, 6, 8, 10, 15, 16, 17, 18, 19, 21, 22, 23, 24]
biochemistry_columns_to_delete: [3, 7]
coagulation_columns_to_delete: [8]

# 动态数据步骤控制配置
dynamic_validation_only: false
dynamic_processing_only: false
skip_interactive: false
verbose: true
```

## 🚀 主要功能

### 动态数据处理模式
- **数据验证**: 验证时间序列CSV文件的结构和数据质量
- **数据处理**: 清理和重命名列，删除指定列
- **步骤控制**: 可配置的验证和处理步骤
- **报告生成**: 详细的验证和处理报告

### 静态数据处理模式
- **标准化编码**: 将中文编码转换为英文标准编码
- **数据类型转换**: 智能分类和数值重新分类
- **日期格式统一**: 标准化日期格式
- **临床变量映射**: 专业的医学术语标准化

## 📊 数据处理流程

### 动态数据验证
1. 检查文件数量是否符合预期
2. 验证每个文件的列数和结构
3. 检查数据类型和格式（数值或NA）
4. 检查时间索引完整性
5. 生成详细验证报告

### 动态数据处理
1. 删除指定的列：
   - CBC列: 002, 004, 006, 008, 010, 015-019, 021-024
   - Biochemistry列: 003, 007
   - Coagulation列: 008
2. 可选删除VCN001和Lymphocyte Subsets列
3. 重命名列以保持连续编号
4. 保存处理后的文件到输出目录
5. 生成处理报告

### 静态数据标准化
1. 读取患者基础信息CSV
2. 标准化性别、疾病类型等分类变量
3. 重新分类数值型变量
4. 统一日期格式
5. 输出标准化数据文件

## 🛠️ 故障排除

### 常见问题及解决方案
- **问题**: 配置文件加载失败
  - **解决方法**: 检查配置文件路径和格式
- **问题**: 数据验证失败
  - **解决方法**: 检查输入数据结构和配置参数

### 调试模式

```bash
# 启用详细输出
python data_processed.py --mode dynamic --verbose --print-config

# 查看完整配置
python data_processed.py --print-config > current_config.txt

# 测试配置而不执行处理
python data_processed.py --print-config --config test_config.yaml
```

## 📁 输入/输出格式

### 动态数据
- **输入**: `processed/` 文件夹中的时间序列CSV文件
- **输出**: 清理后的CSV文件和详细报告

### 静态数据
- **输入**: 包含患者基础信息的CSV文件
- **输出**: 标准化编码后的CSV文件

## 🔧 开发和扩展

模块化设计便于：
- 添加新的数据处理功能
- 扩展配置选项
- 集成到其他系统
- 单元测试和调试

### 项目结构说明

- `data_processed.py`: 主程序入口，协调各个模块
- `utils/`: 工具模块目录，包含核心工具函数
- `dynamic_data_processing/`: 动态数据处理相关模块
- `static_data_processing/`: 静态数据处理相关模块
- `config.yaml`: 主配置文件

---

**⚠️ 重要提示**: 本系统专为CAR-T治疗临床数据处理设计。在处理真实患者数据时，请确保遵循相关医学研究伦理规范和数据保护法规。