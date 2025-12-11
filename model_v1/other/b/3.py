import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt

# --- 1. 加载阶段二处理好的数据 ---
print("步骤 1: 加载预处理后的数据...")
try:
    X = pd.read_csv('X_processed.csv')
    y = pd.read_csv('y_target.csv').squeeze() # .squeeze()将DataFrame转为Series
except FileNotFoundError:
    print("错误: 'X_processed.csv' 或 'y_target.csv' 未找到。请确保您已成功运行阶段二的代码。")
    exit()

print(f"数据加载成功。特征矩阵维度: {X.shape}, 目标向量长度: {len(y)}")

# --- 2. [Step 3.1] 数据集划分 ---
print("\n步骤 3.1: 使用分层抽样划分训练集和测试集...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2, 
    random_state=42, # 保证结果可复现
    stratify=y
)
print(f"训练集大小: {X_train.shape}, 测试集大小: {X_test.shape}")
print(f"训练集中阳性样本比例: {y_train.mean():.2%}")
print(f"测试集中阳性样本比例: {y_test.mean():.2%}")

# --- 3. 数据标准化 ---
print("\n步骤 3: 标准化特征...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
# 转换回DataFrame以便查看列名
X_train_scaled = pd.DataFrame(X_train_scaled, columns=X.columns)
X_test_scaled = pd.DataFrame(X_test_scaled, columns=X.columns)
print("数据标准化完成。")

# --- 4. [Step 3.2] 在训练集上应用SMOTE ---
print("\n步骤 3.2: 在训练集上应用SMOTE处理类别不平衡...")
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)
print(f"SMOTE处理前训练集大小: {X_train_scaled.shape}, 阳性样本数: {y_train.sum()}")
print(f"SMOTE处理后训练集大小: {X_train_resampled.shape}, 阳性样本数: {y_train_resampled.sum()}")

# --- 5. [Step 3.3] 使用XGBoost进行特征选择 ---
print("\n步骤 3.3: 训练初步XGBoost模型以获取特征重要性...")
# 初始化模型
xgb_model_initial = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', use_label_encoder=False, random_state=42)
# 训练模型
xgb_model_initial.fit(X_train_resampled, y_train_resampled)

# 获取并展示特征重要性
feature_importances = pd.Series(xgb_model_initial.feature_importances_, index=X.columns)
# 排序并选择最重要的特征
N_FEATURES = 40 # 我们选择最重要的40个特征
top_features = feature_importances.nlargest(N_FEATURES)

print(f"\n模型识别出的Top {N_FEATURES} 个最重要的特征:")
print(top_features)

# (可选) 绘制特征重要性图
plt.figure(figsize=(10, 10))
top_features.sort_values().plot(kind='barh', title=f'Top {N_FEATURES} Feature Importances from XGBoost')
plt.xlabel('Importance Score')
plt.ylabel('Features')
plt.tight_layout()
plt.show()

# --- 6. [Step 3.4] 使用筛选出的特征训练最终模型 ---
print(f"\n步骤 3.4: 使用Top {N_FEATURES} 个特征训练最终的预测模型...")
# 获取最重要的特征名列表
top_feature_names = top_features.index.tolist()

# 使用这些特征筛选数据集
X_train_final = X_train_resampled[top_feature_names]
X_test_final = X_test_scaled[top_feature_names]

# 初始化并训练最终模型
final_model = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', use_label_encoder=False, random_state=42)
final_model.fit(X_train_final, y_train_resampled)
print("最终模型训练完成。")


# --- 7. 保存最终模型及相关文件以备下一阶段使用 ---
print("\n--- 阶段三完成 ---")
# 保存模型
joblib.dump(final_model, 'final_crs_model.joblib')
# 保存特征列表
joblib.dump(top_feature_names, 'top_features.joblib')
# 保存测试集
joblib.dump((X_test_final, y_test), 'test_data_final.joblib')
# 保存scaler
joblib.dump(scaler, 'scaler.joblib')

print("最终模型、选择的特征列表、标准化器和测试集已保存，准备进入评估阶段。")