import pandas as pd
import numpy as np

# --- 1. 加载阶段一生成的数据 ---
FEATURE_MATRIX_PATH = 'final_feature_matrix.csv'
print(f"步骤 1: 加载特征矩阵 '{FEATURE_MATRIX_PATH}'...")
try:
    df = pd.read_csv(FEATURE_MATRIX_PATH)
except FileNotFoundError:
    print(f"错误: 文件 '{FEATURE_MATRIX_PATH}' 未找到。请确保您已成功运行阶段一的代码。")
    exit()

print(f"数据加载成功。原始维度: {df.shape}")


# --- 2. 定义目标变量 (CRS_target) ---
print("\n步骤 2: 定义二分类目标变量 (CRS_target)...")
# 首先确保CRS grade列是数值类型，非数值转为NaN
df['CRS grade'] = pd.to_numeric(df['CRS grade'], errors='coerce')
# 筛选出 CRS grade 为 0, 1, 2, 3, 4... 的有效行
df_filtered = df.dropna(subset=['CRS grade']).copy()

# 创建目标变量：CRS grade >= 2 为 1, 否则为 0
df_filtered['CRS_target'] = (df_filtered['CRS grade'] >= 2).astype(int)

print("目标变量 'CRS_target' 创建完成。")
print("CRS毒性分布情况:")
print(df_filtered['CRS_target'].value_counts())


# --- 3. 分离特征(X)和目标(y)，并移除无关列 ---
print("\n步骤 3: 分离特征与目标，并移除无关列...")
# 定义目标变量
y = df_filtered['CRS_target']

# 定义需要移除的列
# 包括ID, 原始的目标变量们, 以及日期
cols_to_drop = [
    'PatientID', 
    'CRS grade', 
    'ICANS grade', 
    'Early ICAHT grade',
    'Late ICAHT grade', 
    'Infection grade', 
    'CAR-T cell infusion date',
    'CRS_target' # 从特征矩阵中移除目标本身
]
# 确保只丢弃数据框中实际存在的列
cols_to_drop_existing = [col for col in cols_to_drop if col in df_filtered.columns]
X = df_filtered.drop(columns=cols_to_drop_existing)
print(f"移除了 {len(cols_to_drop_existing)} 个无关列。")


# --- 4. 转换分类特征为数值 (One-Hot Encoding) ---
print("\n步骤 4: 对分类特征进行独热编码...")
# 自动识别 object 和 category 类型的列
categorical_features = X.select_dtypes(include=['object', 'category']).columns
X_processed = pd.get_dummies(X, columns=categorical_features, drop_first=True)
print(f"对 {len(categorical_features)} 个分类特征进行了编码。")
print(f"编码后的特征维度: {X_processed.shape}")


# --- 5. [Step 2.1] 处理缺失值 ---
print("\n步骤 2.1: 使用中位数填充缺失值...")
# 计算每列的中位数
median_imputer = X_processed.median()
# 填充缺失值
X_processed.fillna(median_imputer, inplace=True)
missing_values_after = X_processed.isnull().sum().sum()
print(f"缺失值填充完成。剩余缺失值数量: {missing_values_after}")


# --- 6. [Step 2.2] 通过高相关性筛选特征 ---
print("\n步骤 2.2: 移除高度相关的特征 (阈值 > 0.9)...")
# 计算相关性矩阵
corr_matrix = X_processed.corr().abs()
# 获取上三角矩阵，避免重复比较
upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
# 找到相关性大于阈值的特征列
to_drop_corr = [column for column in upper_tri.columns if any(upper_tri[column] > 0.9)]

# 移除这些列
X_processed = X_processed.drop(columns=to_drop_corr)
print(f"移除了 {len(to_drop_corr)} 个高度相关的特征。")


# --- 7. 输出最终结果 ---
print("\n--- 阶段二完成 ---")
print(f"最终处理后的特征矩阵维度: {X_processed.shape}")
print(f"最终的目标向量长度: {len(y)}")

# 保存处理后的数据以备下一阶段使用
X_processed_path = 'X_processed.csv'
y_target_path = 'y_target.csv'
X_processed.to_csv(X_processed_path, index=False)
y.to_csv(y_target_path, index=False, header=True)
print(f"\n处理后的特征矩阵已保存至: {X_processed_path}")
print(f"目标向量已保存至: {y_target_path}")