# 🚀 快速使用指南

## 立即开始

### 1. 运行修改后的代码

```python
# 在Jupyter中运行单元格23和24
# 单元格23: 嵌套CV特征选择（约需2-5分钟）
# 单元格24: 结果可视化
```

### 2. 查看推荐特征

```python
# 主要推荐（最保守）
print(f"推荐特征数: {len(sig_features_fdr)}")
print(sig_features_fdr)

# 查看稳定性
print(feature_stability[feature_stability['FDR_q005_Stability'] >= 0.6])
```

### 3. 使用特征进行建模

```python
# ✅ 正确用法
X_train_selected = X_train_df[sig_features_fdr]
X_test_selected = X_test_df[sig_features_fdr]

# 继续你的模型训练
model.fit(X_train_selected, y_train)
```

---

## 关键参数调整

### 如果特征太少

```python
# 方法1: 降低稳定性要求
STABILITY_THRESHOLD = 0.4  # 从0.6降到0.4

# 方法2: 使用更宽松的阈值
sig_features = sig_features_fdr_01  # FDR q<0.1而非0.05

# 方法3: 查看所有在至少1折中被选中的特征
all_selected = feature_stability[
    feature_stability['FDR_q005_Count'] > 0
]['Feature'].tolist()
```

### 如果需要更严格

```python
# 方法1: 提高稳定性要求
STABILITY_THRESHOLD = 1.0  # 必须在所有折中都被选中

# 方法2: 使用更严格的FDR阈值
# 在代码中修改
FDR_ALPHA = 0.01  # 从0.05降到0.01

# 重新运行单元格23
```

---

## 常见问题

### Q1: 为什么特征数量比之前少了？

**A**: 这是正常且预期的！之前的方法由于数据泄露，选出了一些**不稳定/过拟合**的特征。新方法只保留真正稳定的特征，虽然数量可能减少，但**质量更高**。

### Q2: 我能用 `univariate_results_full` 吗？

**A**: ❌ **不能用于建模！** 这个变量仅供可视化参考。它是在全数据集上计算的，存在数据泄露风险。

**只使用这些变量**：
- ✅ `sig_features_fdr`
- ✅ `sig_features_fdr_01`
- ✅ `feature_stability`
- ✅ `univariate_results_cv`

### Q3: 如何解释稳定性分数？

**A**: 稳定性分数 = 特征被选中的折数 / 总折数

- `1.0` (100%): 在所有5折中都被选中 → 非常稳定 ⭐⭐⭐⭐⭐
- `0.8` (80%): 在4/5折中被选中 → 稳定 ⭐⭐⭐⭐
- `0.6` (60%): 在3/5折中被选中 → 较稳定 ⭐⭐⭐
- `0.4` (40%): 在2/5折中被选中 → 不太稳定 ⭐⭐
- `0.2` (20%): 仅在1/5折中被选中 → 不稳定 ⭐

### Q4: CV运行时间太长怎么办？

**A**: 可以调整参数：

```python
# 减少CV折数（默认5折）
N_SPLITS = 3  # 改为3折

# 但注意：折数太少会降低稳定性评估的可靠性
# 推荐至少3-5折
```

### Q5: 后续的LASSO、Boruta等是否也需要修改？

**A**: 是的！如果后续还有其他特征选择方法，建议都使用相同的嵌套CV框架。检查：
- 单元格26: LASSO特征选择
- 其他特征选择模块

---

## 输出文件

运行后会生成以下文件：

```
output/feature_selection/
├── univariate_feature_stability_cv.csv          # 特征稳定性统计
├── univariate_logistic_results_reference.csv    # 全数据集参考（仅供参考）
├── univariate_nested_cv_analysis.png            # 可视化图表
└── feature_keep_stats.json                      # 其他统计信息
```

---

## 检查清单

运行新代码后，请确认：

- [ ] 单元格23运行成功，无错误
- [ ] 单元格24生成了6个子图
- [ ] `sig_features_fdr` 包含合理数量的特征（不是0也不是全部）
- [ ] 稳定性分数合理分布（有高稳定性特征）
- [ ] 各折选出的特征数相对稳定（标准差不太大）
- [ ] 输出文件已保存

---

## 需要帮助？

如果遇到问题：

1. **检查数据**: 确保 `X_train_df`, `y_train`, `feature_names` 都已定义
2. **查看错误**: 仔细阅读错误信息，可能是数据格式问题
3. **减少折数**: 尝试 `N_SPLITS=3` 减少运行时间
4. **调整阈值**: 根据需要调整 `STABILITY_THRESHOLD` 和 `FDR_ALPHA`

---

**快速链接**:
- 详细报告: [FEATURE_SELECTION_FIX_REPORT.md](FEATURE_SELECTION_FIX_REPORT.md)
- 修改的单元格: #23, #24
