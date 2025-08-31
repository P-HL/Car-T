# CAR-T Toxicity Prediction System

## 项目概述

这是一个专门用于CAR-T细胞疗法毒性预测的机器学习系统。该系统能够处理混合了静态患者特征和动态监测数据的复杂医学数据，并进行全面的探索性数据分析（EDA）。

## 特性

- 🏥 **医学数据专用**: 专门设计用于处理CAR-T疗法相关的医学数据
- 📊 **混合数据处理**: 同时处理静态患者特征和动态时序监测数据
- 🎯 **多层次目标变量**: 支持二分类、多分类和多标签毒性预测任务
- 📈 **全面EDA**: 生成详细的探索性数据分析报告和可视化
- 🔧 **企业级架构**: 遵循SOLID原则，具有完整的错误处理和日志系统
- ✅ **高质量代码**: 完整的类型注解、单元测试和文档

## 项目结构

```
cart_toxicity_prediction/
├── main.py                    # 主入口文件
├── config.yaml               # 配置文件
├── requirements.txt          # 依赖管理
├── README.md                 # 项目文档
├── src/                      # 源代码
│   ├── interfaces/           # 接口定义
│   ├── services/            # 数据处理服务
│   ├── models/              # 数据模型
│   ├── utils/               # 工具类
│   ├── exceptions/          # 自定义异常
│   ├── analyzers/           # EDA分析器
│   └── controllers/         # 主控制器
├── tests/                   # 单元测试
├── logs/                    # 日志文件
└── outputs/                 # 输出结果
```

## 快速开始

### 1. 环境准备

确保您的系统安装了 Python 3.10+：

```bash
python --version  # 应显示 3.10.x 或更高版本
```

### 2. 安装依赖

```bash
# 克隆或下载项目到本地
cd cart_toxicity_prediction

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置数据路径

编辑 `config.yaml` 文件，设置您的数据路径：

```yaml
data:
  static_file_path: "/path/to/your/encoded.csv"          # 静态数据文件路径
  dynamic_data_folder: "/path/to/your/dynamic_data"      # 动态数据文件夹路径
  max_patients_test: 10                                  # 测试模式患者数量
```

### 4. 运行分析

```bash
python main.py
```

系统将首先运行测试模式（处理少量患者），然后询问是否进行全量分析。

## 数据格式要求

### 静态数据 (encoded.csv)

- **格式**: CSV文件
- **内容**: 每行一个患者，包含以下列：
  - 人口统计学信息：Age, Sex
  - 临床特征：Disease, BM_disease_burden, 等
  - 毒性指标：CRS_grade, ICANS_grade, Early_ICAHT_grade, Late_ICAHT_grade, Infection_grade

### 动态数据

- **格式**: 多个CSV文件，每个患者一个文件
- **命名**: `pt_1.csv`, `pt_2.csv`, ..., `pt_1000.csv`
- **内容**: 每个文件包含该患者100天的监测数据，92个动态变量

## 输出结果

### 1. 可视化图表

在 `outputs/` 文件夹中生成以下图表：

- `missing_values_analysis.png` - 缺失值分析
- `target_distribution.png` - 目标变量分布
- `numeric_distributions.png` - 数值变量分布
- `categorical_distributions.png` - 分类变量分布
- `correlation_heatmap.png` - 相关性热图
- `outlier_summary.png` - 异常值总结
- `dynamic_missing_patterns.png` - 动态数据缺失模式
- `dynamic_temporal_trends.png` - 时序趋势分析
- `dynamic_variable_distributions.png` - 动态变量分布
- `dynamic_patient_variability.png` - 患者间变异性

### 2. 日志文件

在 `logs/` 文件夹中生成详细的分析日志：

- `cart_analysis.log` - 完整的分析过程日志

### 3. 创建的目标变量

系统会自动创建以下目标变量：

- `Overall_Severe_Toxicity` - 总体严重毒性（二分类）
- `Severe_CRS_grade_Occurred` - CRS严重毒性
- `Severe_ICANS_grade_Occurred` - ICANS严重毒性
- `Severe_Early_ICAHT_grade_Occurred` - 早期ICAHT严重毒性
- `Severe_Late_ICAHT_grade_Occurred` - 晚期ICAHT严重毒性
- `Severe_Infection_grade_Occurred` - 感染严重毒性
- `Max_Toxicity_Grade` - 最高毒性等级
- `Severe_Toxicity_Count` - 严重毒性计数
- `Toxicity_Severity_Score` - 毒性严重程度评分

## 快速使用指南

运行系统前，请先修改配置文件中的数据路径，然后直接运行：

```bash
python main.py
```
------------------------------------------------------------------------------------
