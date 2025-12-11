# 数据分割器模块 (Data Splitters)

## 📋 概述

本模块提供两个专为医疗数据设计的数据分割类，用于替代 `sklearn.model_selection.train_test_split`，解决患者级数据独立性问题。

### 核心特性

- ✅ **患者级独立性**：确保同一患者的数据不会同时出现在训练集和测试集中
- ✅ **分层抽样**：保持训练集和测试集中类别比例与总体一致
- ✅ **可复现性**：固定随机种子可以重现相同的划分结果
- ✅ **兼容sklearn**：提供与 `train_test_split` 类似的接口，易于集成
- ✅ **交叉验证支持**：可选的Group-Stratified交叉验证功能

---

## 📦 模块内容

### 1. `PatientLevelStratifiedSplitter`

基础的患者级分层分割器，实现70/30（或自定义比例）的训练测试划分。

**适用场景**：
- 简单的训练/测试划分
- 不需要交叉验证的场景
- 直接替换 `train_test_split`

### 2. `PatientLevelStratifiedSplitterWithCV`

增强版分割器，在训练集上额外创建k折交叉验证。

**适用场景**：
- 需要超参数调优
- 需要评估模型稳定性
- 需要多折验证的实验设计

### 3. `patient_level_train_test_split`

兼容函数，提供与 `train_test_split` 相同的接口。

**适用场景**：
- 快速替换现有代码
- 最小化代码改动
- 保持与sklearn风格一致

---

## 🚀 快速开始

### 安装依赖

```bash
pip install pandas numpy scikit-learn
```

### 基础用法

```python
from pipeline.data_splitters import PatientLevelStratifiedSplitter

# 创建分割器
splitter = PatientLevelStratifiedSplitter(test_size=0.3, random_state=42)

# 执行划分
train_df, test_df = splitter.split(
    df, 
    label_col="label",           # 标签列名
    patient_id_col="patient_id"  # 患者ID列名
)
```

### 使用兼容函数（推荐用于快速替换）

```python
from pipeline.data_splitters import patient_level_train_test_split

# 替换原有的 train_test_split
train_df, test_df = patient_level_train_test_split(
    df,
    label_col="label",
    patient_id_col="patient_id",
    test_size=0.3,
    random_state=42
)
```

---

## 📖 详细使用指南

### 示例1: 替换 model.py 中的 train_test_split

**原始代码 (model.py 第11行附近)：**

```python
from sklearn.model_selection import train_test_split

df = pd.read_csv("encoded_standardized.csv")
df["label"] = (df["infection_grade"] > 2).astype(int)

train_df, test_df = train_test_split(
    df, 
    test_size=0.3, 
    stratify=df["label"], 
    random_state=42
)
```

**修改后的代码：**

```python
from pipeline.data_splitters import patient_level_train_test_split

df = pd.read_csv("encoded_standardized.csv")
df["label"] = (df["infection_grade"] > 2).astype(int)

# 直接替换，添加patient_id_col参数
train_df, test_df = patient_level_train_test_split(
    df,
    label_col="label",
    patient_id_col="patient_id",  # ← 新增：确保患者级独立
    test_size=0.3,
    random_state=42
)

# 后续代码完全不变
```

### 示例2: 使用交叉验证进行超参数调优

```python
from pipeline.data_splitters import PatientLevelStratifiedSplitterWithCV

# 创建带CV的分割器
splitter = PatientLevelStratifiedSplitterWithCV(
    test_size=0.3, 
    n_folds=5,      # 5折交叉验证
    random_state=42
)

# 执行划分
train_df, test_df, cv_folds = splitter.split(
    df, 
    label_col="label", 
    patient_id_col="patient_id"
)

# 使用交叉验证
from sklearn.metrics import roc_auc_score

cv_scores = []
for fold_idx, (train_ids, val_ids) in enumerate(cv_folds, 1):
    # 根据患者ID筛选数据
    fold_train = train_df[train_df["patient_id"].isin(train_ids)]
    fold_val = train_df[train_df["patient_id"].isin(val_ids)]
    
    # 训练模型
    model = your_model_pipeline()
    model.fit(fold_train, fold_train["label"])
    
    # 验证
    val_pred = model.predict_proba(fold_val)[:, 1]
    auc = roc_auc_score(fold_val["label"], val_pred)
    cv_scores.append(auc)
    print(f"Fold {fold_idx} AUC: {auc:.4f}")

print(f"平均 AUC: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
```

### 示例3: 保存折叠信息以供后续使用

```python
import os
import numpy as np

# 执行划分
splitter = PatientLevelStratifiedSplitterWithCV(
    test_size=0.3, n_folds=5, random_state=42
)
train_df, test_df, cv_folds = splitter.split(
    df, label_col="label", patient_id_col="patient_id"
)

# 创建输出目录
output_dir = "./output/cv_splits"
os.makedirs(output_dir, exist_ok=True)

# 保存主划分
train_df.to_csv(os.path.join(output_dir, "train_static.csv"), index=False)
test_df.to_csv(os.path.join(output_dir, "test_static.csv"), index=False)

# 保存交叉验证折叠
for i, (train_ids, val_ids) in enumerate(cv_folds, 1):
    np.savetxt(
        os.path.join(output_dir, f"fold{i}_train_ids.txt"), 
        train_ids, fmt="%s"
    )
    np.savetxt(
        os.path.join(output_dir, f"fold{i}_val_ids.txt"), 
        val_ids, fmt="%s"
    )

print(f"折叠信息已保存到: {output_dir}")
```

---

## 🔄 与原始脚本的对应关系

### split_BNHL_CRS_dataset.py → PatientLevelStratifiedSplitter

| 原始脚本功能 | 对应类方法 | 说明 |
|------------|-----------|------|
| StratifiedShuffleSplit | `split()` | 分层70/30划分 |
| 患者级独立性 | 自动实现 | 通过patient_id_col参数 |
| 统计信息输出 | `verbose=True` | 自动打印统计 |
| 元数据保存 | `get_split_info()` | 获取划分信息字典 |

**重构优势**：
- ❌ 不再需要手动管理文件复制
- ❌ 不再需要创建输出目录结构
- ✅ 专注于数据划分逻辑
- ✅ 可与任何Pipeline无缝集成

### split_BNHL_CRS_dataset_with_innerCV.py → PatientLevelStratifiedSplitterWithCV

| 原始脚本功能 | 对应类方法 | 说明 |
|------------|-----------|------|
| 主70/30划分 | `split()` | 返回train_df, test_df |
| 5折Group-Stratified | `split()` | 返回cv_folds列表 |
| fold文件保存 | 用户自行保存 | 提供ID列表供保存 |
| 元数据记录 | `get_split_info()` | 包含CV配置信息 |

**重构优势**：
- ✅ 代码更简洁（从200+行降至50行调用）
- ✅ 更灵活的使用方式
- ✅ 易于集成到现有Pipeline
- ✅ 支持自定义fold数量

---

## ⚙️ API 参考

### PatientLevelStratifiedSplitter

```python
PatientLevelStratifiedSplitter(
    test_size=0.3,      # 测试集比例
    random_state=42,    # 随机种子
    verbose=True        # 是否打印统计信息
)
```

**方法**：

- `split(df, label_col, patient_id_col="patient_id")` → `(train_df, test_df)`
- `get_split_info()` → `dict` - 返回划分配置信息

### PatientLevelStratifiedSplitterWithCV

```python
PatientLevelStratifiedSplitterWithCV(
    test_size=0.3,      # 测试集比例
    n_folds=5,          # 交叉验证折数
    random_state=42,    # 随机种子
    verbose=True        # 是否打印统计信息
)
```

**方法**：

- `split(df, label_col, patient_id_col="patient_id")` → `(train_df, test_df, cv_folds)`
- `get_split_info()` → `dict` - 返回划分和CV配置信息

**cv_folds 格式**：

```python
# cv_folds 是一个列表，每个元素是一个元组
cv_folds = [
    (fold1_train_patient_ids, fold1_val_patient_ids),
    (fold2_train_patient_ids, fold2_val_patient_ids),
    ...,
    (fold5_train_patient_ids, fold5_val_patient_ids)
]

# 使用示例
for train_ids, val_ids in cv_folds:
    fold_train = train_df[train_df["patient_id"].isin(train_ids)]
    fold_val = train_df[train_df["patient_id"].isin(val_ids)]
```

---

## ⚠️ 注意事项

### 数据要求

1. **患者ID列必须存在**：数据框必须包含唯一的患者标识列
2. **标签列类型**：支持二分类(0/1)和多分类的离散标签
3. **每行代表一个患者**：输入数据应该是患者级的静态数据

### 最佳实践

1. **先划分，后预处理**：
   ```python
   # ✅ 正确：先划分再fit
   train_df, test_df = splitter.split(df, ...)
   pipeline.fit(train_df, train_df["label"])
   pipeline.transform(test_df)
   
   # ❌ 错误：先预处理再划分（可能导致数据泄漏）
   df_processed = pipeline.fit_transform(df)
   train_df, test_df = splitter.split(df_processed, ...)
   ```

2. **固定随机种子**：
   ```python
   # 确保实验可复现
   splitter = PatientLevelStratifiedSplitter(random_state=42)
   ```

3. **检查类别平衡**：
   ```python
   # 使用verbose=True查看统计信息
   splitter = PatientLevelStratifiedSplitter(verbose=True)
   train_df, test_df = splitter.split(df, ...)
   ```

### 常见问题

**Q: 为什么不能用普通的 train_test_split？**

A: 医疗数据中，同一患者可能有多条时序记录。如果使用普通划分，同一患者的数据可能同时出现在训练集和测试集中，导致数据泄漏，高估模型性能。

**Q: 交叉验证时测试集会参与吗？**

A: 不会。交叉验证只在训练集上进行。测试集始终保持独立，仅用于最终评估。

**Q: 如何处理极度不平衡的数据？**

A: 分割器已经使用分层抽样保持比例。如果正样本非常少（<5个），建议：
- 收集更多数据
- 使用SMOTE等过采样技术（在划分后应用）
- 减少交叉验证折数（如3折而非5折）

---

## 📊 性能对比

| 指标 | 原始脚本 | 新分割器类 |
|-----|---------|-----------|
| 代码行数 | ~300行 | ~50行调用 |
| 配置灵活性 | 低（硬编码） | 高（参数化） |
| 可复用性 | 低 | 高 |
| sklearn集成 | 需手动适配 | 原生兼容 |
| 学习曲线 | 陡峭 | 平缓 |

---

## 🤝 贡献

如有问题或建议，欢迎提Issue或Pull Request。

---

## 📄 许可证

MIT License

---

## 📚 相关文档

- [scikit-learn 数据分割文档](https://scikit-learn.org/stable/modules/cross_validation.html)
- [医疗AI中的数据泄漏问题](https://arxiv.org/abs/2008.05815)
- [GroupKFold 最佳实践](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html)

---

**最后更新**: 2025-11-20  
**维护者**: AI Assistant
