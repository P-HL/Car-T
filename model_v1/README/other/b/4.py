import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib.pyplot as plt
from sklearn.metrics import (
    classification_report, 
    roc_auc_score, 
    roc_curve, 
    precision_recall_curve, 
    auc
)

# --- 1. 加载阶段三保存的资产 ---
print("步骤 1: 加载模型、特征列表和测试数据...")
try:
    final_model = joblib.load('final_crs_model.joblib')
    top_feature_names = joblib.load('top_features.joblib')
    X_test_final, y_test = joblib.load('test_data_final.joblib')
    # 我们需要原始数据来获取疾病类型
    original_df = pd.read_csv('final_feature_matrix.csv')
except FileNotFoundError:
    print("错误: 找不到阶段三生成的文件。请确保您已成功运行阶段三的代码。")
    exit()

print("资产加载成功。")

# --- 2. [Step 4.1] 在测试集上进行性能评估 ---
print("\n步骤 4.1: 在测试集上评估模型性能...")
# 进行预测
y_pred = final_model.predict(X_test_final)
y_pred_proba = final_model.predict_proba(X_test_final)[:, 1] # 获取阳性类的概率

# 打印分类报告
print("\n分类报告:")
print(classification_report(y_test, y_pred, target_names=['CRS Grade < 2', 'CRS Grade >= 2']))

# 计算AUC分数
auc_roc = roc_auc_score(y_test, y_pred_proba)
precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
auc_pr = auc(recall, precision)

print(f"AUC-ROC Score: {auc_roc:.4f}")
print(f"AUC-PR Score: {auc_pr:.4f}")

# 绘制ROC和PR曲线
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# ROC Curve
fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
ax1.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {auc_roc:.2f})')
ax1.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
ax1.set_xlim([0.0, 1.0])
ax1.set_ylim([0.0, 1.05])
ax1.set_xlabel('False Positive Rate')
ax1.set_ylabel('True Positive Rate')
ax1.set_title('Receiver Operating Characteristic (ROC) Curve')
ax1.legend(loc="lower right")

# Precision-Recall Curve
ax2.plot(recall, precision, color='blue', lw=2, label=f'PR curve (area = {auc_pr:.2f})')
ax2.set_xlabel('Recall')
ax2.set_ylabel('Precision')
ax2.set_title('Precision-Recall Curve')
ax2.legend(loc="lower left")

plt.tight_layout()
plt.show()


# --- 3. [Step 4.2] 模型可解释性分析 (SHAP) ---
print("\n步骤 4.2: 使用SHAP进行模型可解释性分析...")
# 创建SHAP explainer
explainer = shap.TreeExplainer(final_model)
# 计算测试集的SHAP值
shap_values = explainer.shap_values(X_test_final)

# 全局解释：绘制SHAP摘要图
print("正在生成SHAP摘要图 (全局特征重要性)...")
shap.summary_plot(shap_values, X_test_final, plot_type="bar", show=False)
plt.title("SHAP Summary Plot: Top Feature Importance")
plt.show()

shap.summary_plot(shap_values, X_test_final, show=False)
plt.title("SHAP Beeswarm Plot: Feature Impact on Model Output")
plt.show()


# 局部解释：解释单个高风险患者的预测
print("\n为单个高风险患者生成SHAP力图 (局部解释)...")
# 找到一个被正确预测为阳性(1)的样本
correctly_predicted_positives = np.where((y_test == 1) & (y_pred == 1))[0]
if len(correctly_predicted_positives) > 0:
    idx_to_explain = correctly_predicted_positives[0]
    
    print(f"解释样本索引: {X_test_final.index[idx_to_explain]}")
    print(f"真实标签: {y_test.iloc[idx_to_explain]}, 预测概率: {y_pred_proba[idx_to_explain]:.3f}")
    
    # 初始化JS环境以便绘图
    shap.initjs()
    # 创建并显示力图
    display(shap.force_plot(explainer.expected_value, shap_values[idx_to_explain,:], X_test_final.iloc[idx_to_explain,:]))
else:
    print("测试集中没有找到被正确预测为阳性的样本，无法生成局部解释图。")


# --- 4. [Step 4.3] 稳健性检验 ---
print("\n步骤 4.3: 在不同疾病亚组上进行稳健性检验...")
# 获取测试集样本的原始疾病信息
test_indices = X_test_final.index
original_test_info = original_df.iloc[test_indices]

# 合并疾病类型和预测结果
test_results = pd.DataFrame({
    'Disease': original_test_info['Disease'].values,
    'y_test': y_test.values,
    'y_pred_proba': y_pred_proba
})

# 计算每个亚组的AUC
subgroup_aucs = test_results.groupby('Disease').apply(
    lambda g: roc_auc_score(g['y_test'], g['y_pred_proba']) if len(g['y_test'].unique()) > 1 else np.nan
)
print("\n模型在不同疾病亚组上的AUC-ROC表现:")
print(subgroup_aucs)