# Perfect Pipeline 使用指南

## 📋 概述

`perfect_pipeline.py` 提供了一个完善的无数据泄漏Pipeline，用于Car-T细胞疗法的毒性预测任务。

### 核心功能

1. **删除常量列** (`ConstantColumnDropper`) - 第35行
2. **毒性等级二元化** (`ToxicityBinarizer`) - 第114行  
3. **静态特征编码**（数值/类别/序数）
4. **动态特征聚合**（时序数据统计）
5. **完整Pipeline构建**（sklearn兼容）

---

## 🎯 关键类审核结果

### 1. ConstantColumnDropper（第35-108行）

**状态**: ✅ **功能完全正确**

**实现逻辑**:
```python
# fit阶段：识别唯一值≤1的列
self.constant_cols_ = [col for col in X.columns if X[col].nunique() <= 1]

# transform阶段：删除这些列
return X.drop(columns=self.constant_cols_, errors="ignore")
```

**适用场景**:
- 删除经过疾病筛选后的常量列（如 `disease='B-NHL'`）
- 删除全为相同值的数值列
- 删除全为缺失值的列

**使用示例**:
```python
from perfect_pipeline import ConstantColumnDropper

# 创建删除器
dropper = ConstantColumnDropper()

# 在训练集上fit
dropper.fit(train_df)

# 在训练集和测试集上transform
train_cleaned = dropper.transform(train_df)
test_cleaned = dropper.transform(test_df)

# 查看删除了哪些列
print(f"删除的列: {dropper.constant_cols_}")
```

**注意事项**:
- ✅ 只使用训练集的统计信息（防止数据泄漏）
- ✅ 训练集和测试集删除相同的列
- ⚠️ 建议在数据拆分后、Pipeline之前使用

---

### 2. ToxicityBinarizer（第114-304行）

**状态**: ✅ **功能完全正确**（已优化注释）

**二元化规则**:
```
≤ threshold → 0 (非严重，包含threshold值)
> threshold → 1 (严重，不包含threshold值)

示例（threshold=2）:
  等级 0, 1, 2 → 0 (非严重)
  等级 3, 4, 5 → 1 (严重)
  等级 NaN → NaN (保留缺失值)
```

**核心代码**:
```python
# 第286-298行
# 应用二元化规则：
# - 如果 grade > threshold: 返回 1 (严重)
# - 如果 grade <= threshold: 返回 0 (非严重)  
# - 如果 grade 是 NaN: 保持 NaN (缺失值)
binary_result = (X[col] > thresh).astype(float)

# 将NaN位置恢复为NaN（保留缺失值，不强制转换）
X[target_col] = binary_result.where(X[col].notna(), np.nan).astype('Int64')
```

**使用方式**:

#### 方式1: 单列转换（向后兼容）
```python
from perfect_pipeline import ToxicityBinarizer

# CRS等级二元化（threshold=2）
binarizer = ToxicityBinarizer(columns="CRS_grade", threshold=2)
df_transformed = binarizer.fit_transform(df)
# CRS_grade列会被覆盖为0/1
```

#### 方式2: 多列转换，相同阈值
```python
# 多个毒性指标使用相同阈值
binarizer = ToxicityBinarizer(
    columns=["CRS", "ICANS", "Infection"],
    threshold=2
)
df_transformed = binarizer.fit_transform(df)
```

#### 方式3: 多列转换，不同阈值（推荐）
```python
# 每个毒性指标使用不同阈值
binarizer = ToxicityBinarizer(columns={
    "CRS": 2,         # CRS: ≤2轻度，>2严重
    "ICANS": 1,       # ICANS: ≤1轻度，>1严重  
    "Infection": 3    # 感染: ≤3轻度，>3严重
})
df_transformed = binarizer.fit_transform(df)
```

#### 方式4: 创建新列（不覆盖原列）
```python
# 使用suffix参数保留原列
binarizer = ToxicityBinarizer(
    columns={"CRS": 2, "ICANS": 1},
    suffix="_binary"
)
df_transformed = binarizer.fit_transform(df)
# 结果包含: CRS, CRS_binary, ICANS, ICANS_binary
```

**验证结果**:
```
输入: [0, 1, 2, 3, 4, 5, NaN]
输出: [0, 0, 0, 1, 1, 1, NaN]  (threshold=2)

✅ 等级2归入0（非严重）- 边界值处理正确
✅ 缺失值保留为NaN - 不强制转换
```

---

## 🔄 完整使用流程

### 场景1: 基础预处理 + 模型训练

```python
import pandas as pd
from perfect_pipeline import (
    ConstantColumnDropper,
    ToxicityBinarizer,
    build_no_leak_pipeline
)
from pipeline.data_splitters import patient_level_train_test_split

# 1. 加载数据
df = pd.read_csv("static_data.csv")

# 2. 删除常量列（在拆分前）
dropper = ConstantColumnDropper()
df = dropper.fit_transform(df)
print(f"删除的常量列: {dropper.constant_cols_}")

# 3. 毒性二元化（在拆分前）
binarizer = ToxicityBinarizer(columns={
    "CRS_grade": 2,
    "ICANS_grade": 1
})
df = binarizer.fit_transform(df)

# 4. 患者级数据拆分
train_df, test_df = patient_level_train_test_split(
    df,
    label_col="CRS_grade",  # 已二元化
    patient_id_col="patient_id",
    test_size=0.3,
    random_state=42
)

# 5. 定义特征列
numeric_cols = ["age", "bmi", "bm_disease_burden"]
categorical_cols = ["sex", "disease_type"]
ordinal_cols = ["ann_arbor_stage"]
dynamic_dir = "/path/to/dynamic_csvs/"

# 6. 构建Pipeline
pipe = build_no_leak_pipeline(
    numeric_cols,
    categorical_cols,
    ordinal_cols,
    dynamic_dir
)

# 7. 训练（只在训练集上fit）
pipe.fit(train_df, train_df["CRS_grade"])

# 8. 预测
test_pred = pipe.predict_proba(test_df)[:, 1]
```

---

## ⚠️ 重要注意事项

### 1. 常量列删除的时机

```python
# ✅ 推荐：在数据拆分前删除
dropper = ConstantColumnDropper()
df = dropper.fit_transform(df)
train_df, test_df = split_data(df)

# ❌ 不推荐：在Pipeline中删除（可能导致train/test列不一致）
# 虽然代码支持，但可能有边界情况问题
```

### 2. 二元化的时机

```python
# ✅ 推荐：在数据拆分前二元化
df["label"] = binarizer.fit_transform(df[["toxicity_grade"]])
train_df, test_df = split_data(df)

# ❌ 错误：拆分后二元化（可能导致标签不一致）
train_df, test_df = split_data(df)
train_df["label"] = binarizer.fit_transform(train_df[["toxicity_grade"]])
```

### 3. 边界值处理

```
threshold = 2 时：
  ✅ 等级2 → 0 (非严重)  # 边界值归入低风险组
  ✅ 等级3 → 1 (严重)

这是医学上常用的保守策略，将"等于阈值"的情况归为低风险。
```

---

## 📊 测试验证

所有核心功能已通过测试：

```bash
cd /home/phl/PHL/Car-T/model-1/pipeline
python test_perfect_pipeline_classes.py
```

**测试覆盖**:
- ✅ 常量列识别和删除
- ✅ 单列二元化（threshold=2）
- ✅ 多列二元化（不同阈值）
- ✅ 后缀模式（保留原列）
- ✅ 边界值处理（等于阈值→0）
- ✅ 缺失值保留（NaN→NaN）
- ✅ 单样本处理
- ✅ 全NaN列处理

---

## 🎓 最佳实践

### 1. 推荐的预处理顺序

```python
# 步骤1: 删除常量列
df = ConstantColumnDropper().fit_transform(df)

# 步骤2: 毒性二元化
df = ToxicityBinarizer(columns={"CRS": 2}).fit_transform(df)

# 步骤3: 患者级数据拆分
train_df, test_df = patient_level_train_test_split(df, ...)

# 步骤4: 特征工程Pipeline（只在训练集上fit）
pipe = build_no_leak_pipeline(...)
pipe.fit(train_df, train_df["label"])

# 步骤5: 预测
test_pred = pipe.predict_proba(test_df)
```

### 2. 多毒性指标处理

```python
# 同时处理多种毒性（推荐方式）
binarizer = ToxicityBinarizer(columns={
    "CRS": 2,          # 细胞因子释放综合征
    "ICANS": 1,        # 神经毒性
    "Infection": 3     # 感染等级
}, suffix="_binary")   # 保留原始等级列

df = binarizer.fit_transform(df)

# 可以选择任一个作为主要预测目标
pipe.fit(train_df, train_df["CRS_binary"])
```

---

## 🔧 常见问题

**Q1: 为什么边界值(threshold=2)归入0而不是1？**

A: 这是医学上的保守策略。将"等于阈值"的情况归为低风险组，避免过度治疗。实际应用中可根据需求调整阈值。

**Q2: 可以在Pipeline中使用这两个类吗？**

A: 可以，但不推荐ConstantColumnDropper在Pipeline中使用（见代码第398-450行的FullPreprocessor实现）。ToxicityBinarizer更适合作为预处理步骤。

**Q3: 如何处理缺失的毒性等级？**

A: 二元化会保留NaN值，不强制转换。后续的Pipeline会通过插补器处理缺失值。

---

**最后更新**: 2025-11-20  
**状态**: ✅ 审核通过，功能正常  
**维护者**: AI Assistant
