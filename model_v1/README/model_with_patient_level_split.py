"""
model.py - 使用患者级分层分割器的示例
================================================

这是原始 model.py 文件的修改版本，展示如何使用新的数据分割器类。

修改内容:
1. 导入语句修改（第1行）
2. 数据划分调用修改（第11行附近）
3. 其余代码完全不变

作者: AI Assistant
日期: 2025-11-20
"""

# ============================================================
# 方案A: 使用兼容函数（推荐 - 最小改动）
# ============================================================

# 修改前（原始代码）:
# from sklearn.model_selection import train_test_split

# 修改后:
from pipeline.data_splitters import patient_level_train_test_split
from pipeline.perfect_pipeline import build_no_leak_pipeline
import pandas as pd

# 1. 读入静态数据
df = pd.read_csv("encoded_standardized.csv")

# 2. 毒性二元化（安全）
df["label"] = (df["infection_grade"] > 2).astype(int)

# 3. 划分数据（必须在预处理前）
# 修改前:
# train_df, test_df = train_test_split(df, test_size=0.3, 
#                                      stratify=df["label"], random_state=42)

# 修改后（仅添加两个参数）:
train_df, test_df = patient_level_train_test_split(
    df, 
    label_col="label",           # 明确指定标签列
    patient_id_col="patient_id", # 新增：确保患者级独立性
    test_size=0.3, 
    random_state=42
)

# 4. 定义变量类型（完全不变）
numeric_cols = ["age", "bm_disease_burden", ...]  # ... 更多列
categorical_cols = ["sex", "bridging_therapy", ...]  # ... 更多列
ordinal_cols = ["ann_arbor_stage", ...]  # ... 更多列

dynamic_dir = "/home/.../processed_standardized/"

# 5. 构建 Pipeline（完全不变）
pipe = build_no_leak_pipeline(numeric_cols, categorical_cols, ordinal_cols, dynamic_dir)

# 6. 在训练集上 fit（所有统计量仅在训练集计算）（完全不变）
pipe.fit(train_df, train_df["label"])

# 7. 在测试集 transform + predict（完全不变）
pred_prob = pipe.predict_proba(test_df)[:, 1]


# ============================================================
# 方案B: 使用类（更灵活，但需要更多修改）
# ============================================================

"""
from pipeline.data_splitters import PatientLevelStratifiedSplitter
from pipeline.perfect_pipeline import build_no_leak_pipeline
import pandas as pd

# 1. 读入静态数据
df = pd.read_csv("encoded_standardized.csv")

# 2. 毒性二元化（安全）
df["label"] = (df["infection_grade"] > 2).astype(int)

# 3. 创建分割器并划分数据
splitter = PatientLevelStratifiedSplitter(test_size=0.3, random_state=42)
train_df, test_df = splitter.split(
    df, 
    label_col="label", 
    patient_id_col="patient_id"
)

# 可选：打印划分信息
print(f"划分信息: {splitter.get_split_info()}")

# 4-7. 后续代码完全不变
numeric_cols = ["age", "bm_disease_burden"]
categorical_cols = ["sex", "bridging_therapy"]
ordinal_cols = ["ann_arbor_stage"]
dynamic_dir = "/home/.../processed_standardized/"

pipe = build_no_leak_pipeline(numeric_cols, categorical_cols, ordinal_cols, dynamic_dir)
pipe.fit(train_df, train_df["label"])
pred_prob = pipe.predict_proba(test_df)[:, 1]
"""


# ============================================================
# 方案C: 使用带交叉验证的类（用于超参数调优）
# ============================================================

"""
from pipeline.data_splitters import PatientLevelStratifiedSplitterWithCV
from pipeline.perfect_pipeline import build_no_leak_pipeline
from sklearn.metrics import roc_auc_score
import pandas as pd
import numpy as np

# 1. 读入静态数据
df = pd.read_csv("encoded_standardized.csv")

# 2. 毒性二元化（安全）
df["label"] = (df["infection_grade"] > 2).astype(int)

# 3. 创建带CV的分割器并划分数据
splitter = PatientLevelStratifiedSplitterWithCV(
    test_size=0.3, 
    n_folds=5,  # 5折交叉验证
    random_state=42
)
train_df, test_df, cv_folds = splitter.split(
    df, 
    label_col="label", 
    patient_id_col="patient_id"
)

# 4. 定义变量类型
numeric_cols = ["age", "bm_disease_burden"]
categorical_cols = ["sex", "bridging_therapy"]
ordinal_cols = ["ann_arbor_stage"]
dynamic_dir = "/home/.../processed_standardized/"

# 5. 使用交叉验证进行模型评估或超参数调优
print("\\n开始5折交叉验证...")
cv_scores = []

for fold_idx, (train_ids, val_ids) in enumerate(cv_folds, 1):
    print(f"\\n--- Fold {fold_idx} ---")
    
    # 根据患者ID筛选数据
    fold_train = train_df[train_df["patient_id"].isin(train_ids)]
    fold_val = train_df[train_df["patient_id"].isin(val_ids)]
    
    # 构建Pipeline
    pipe = build_no_leak_pipeline(numeric_cols, categorical_cols, ordinal_cols, dynamic_dir)
    
    # 训练
    pipe.fit(fold_train, fold_train["label"])
    
    # 验证
    val_pred = pipe.predict_proba(fold_val)[:, 1]
    auc = roc_auc_score(fold_val["label"], val_pred)
    cv_scores.append(auc)
    
    print(f"Fold {fold_idx} AUC: {auc:.4f}")

# 打印交叉验证结果
print(f"\\n平均CV AUC: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")

# 6. 最终在整个训练集上训练模型
print("\\n在完整训练集上训练最终模型...")
final_pipe = build_no_leak_pipeline(numeric_cols, categorical_cols, ordinal_cols, dynamic_dir)
final_pipe.fit(train_df, train_df["label"])

# 7. 在测试集上评估最终模型
test_pred = final_pipe.predict_proba(test_df)[:, 1]
test_auc = roc_auc_score(test_df["label"], test_pred)
print(f"最终测试集 AUC: {test_auc:.4f}")
"""


# ============================================================
# 总结：三种方案对比
# ============================================================

"""
┌─────────────┬──────────────┬────────────────┬─────────────────┐
│    方案     │   代码改动   │    灵活性      │    推荐场景     │
├─────────────┼──────────────┼────────────────┼─────────────────┤
│ 方案A       │ 最小（2行）  │ 中             │ 快速替换        │
│ 兼容函数    │              │                │ 日常使用        │
├─────────────┼──────────────┼────────────────┼─────────────────┤
│ 方案B       │ 中等（5行）  │ 高             │ 需要获取        │
│ 基础类      │              │                │ 划分信息        │
├─────────────┼──────────────┼────────────────┼─────────────────┤
│ 方案C       │ 较大（20行） │ 最高           │ 超参数调优      │
│ 带CV的类    │              │                │ 模型稳定性评估  │
└─────────────┴──────────────┴────────────────┴─────────────────┘

推荐使用方案A（兼容函数），因为：
✅ 最小化代码改动
✅ 保持与sklearn风格一致
✅ 易于理解和维护
✅ 满足大多数使用场景

如果需要交叉验证，再考虑升级到方案C。
"""
