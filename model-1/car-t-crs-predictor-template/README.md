# CAR-T CRS Predictor Template
详见说明文档内容。

## 📁 仓库结构
```
car-t-crs-predictor/
├─ README.md
├─ requirements.txt
├─ config/
│  └─ config.yaml
├─ data/
│  ├─ static/encoded_standardized.csv
│  └─ dynamic/processed_standardized/
│     ├─ 1.csv
│     ├─ 2.csv
│     └─ ...
├─ split/
│  ├─ main_split.py
│  └─ inner_cv.py
├─ features/
│  ├─ aggregation.py
│  └─ builders.py
├─ pipeline/
│  └─ preprocess.py
├─ train/
│  ├─ cv_train.py
│  ├─ final_train.py
│  └─ search_spaces.py
├─ eval/
│  ├─ evaluate.py
│  └─ plots.py
├─ explain/
│  └─ shap_explain.py
├─ utils/
│  ├─ io_utils.py
│  ├─ config_utils.py
│  └─ logging_utils.py
└─ cli/
   ├─ run_split.py
   ├─ run_train_cv.py
   ├─ run_train_final.py
   ├─ run_evaluate.py
   └─ run_explain.py
```

## ⚙️ 主要设计原则
	1.	所有预处理步骤在训练折内 fit，防止数据泄漏。
	2.	动态数据严格限定时间窗口（Day ≤ +2）。
	3.	以 AUPRC 为主优化指标，兼顾 ROC-AUC 与校准度。
	4.	结果含置信区间与可解释性输出，符合科研复现标准。

## 📂 输出结构
```
artifacts/
├─ models/
│  ├─ fold1_model.pkl
│  └─ final_model.pkl
├─ reports/
│  ├─ cv_metrics_summary.csv
│  ├─ test_metrics.csv
│  ├─ ROC_curve.png
│  └─ shap_summary.png
└─ metadata.yaml
```

# CAR-T CRS Predictor Template

## 📖 项目简介
本模板旨在构建一个基于机器学习的临床毒性预测管线，用于预测 **B-NHL 患者的严重 CRS 风险**。
它实现了从数据处理、特征工程、模型训练、验证到解释的完整流程。

---

## 🧩 核心架构

| 模块 | 功能 |
|------|------|
| `split/` | 数据划分：70/30 外层 + 训练集 5 折内层 |
| `features/` | 动态数据聚合、静态数据对齐 |
| `pipeline/` | 数据预处理（插补/编码/缩放） |
| `train/` | 模型训练、交叉验证、超参数调优 |
| `eval/` | 测试集性能评估与可视化 |
| `explain/` | 模型可解释性（SHAP 分析） |
| `utils/` | 通用配置、日志与 I/O 工具 |
| `cli/` | 命令行脚本入口，串联整个流程 |

---

## 🚀 使用方法

```bash
# Step 1: 安装依赖
pip install -r requirements.txt

# Step 2: 执行数据划分
python cli/run_split.py

# Step 3: 运行5折CV+调参
python cli/run_train_cv.py

# Step 4: 使用最优参数训练最终模型
python cli/run_train_final.py

# Step 5: 在测试集上评估
python cli/run_evaluate.py

# Step 6: 生成可解释性结果
python cli/run_explain.py