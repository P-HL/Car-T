import pandas as pd
import numpy as np
import os
import glob
from scipy.stats import linregress
from tqdm import tqdm # 用于显示进度条，可先通过 pip install tqdm 安装

# --- 1. 配置您的数据路径 ---
STATIC_DATA_PATH = '/home/phl/PHL/Car-T/data_encoder/output/dataset/encoded_standardized.csv'
DYNAMIC_DATA_FOLDER = '/home/phl/PHL/Car-T/data_encoder/output/dataset/processed_standardized'

# --- 2. [Step 1.1] 加载静态数据 ---
print("步骤 1.1: 加载静态数据...")
static_df = pd.read_csv(STATIC_DATA_PATH)
# 假设第一列是患者ID，我们将其重命名以便于合并
patient_id_col = static_df.columns[0]
static_df.rename(columns={patient_id_col: 'PatientID'}, inplace=True)
print(f"静态数据加载完成，包含 {static_df.shape[0]} 位患者, {static_df.shape[1]} 个特征。")

# --- 3. [Step 1.2] 动态数据处理与特征工程 ---
print("\n步骤 1.2: 开始处理动态数据并进行特征工程...")
dynamic_files = sorted(glob.glob(os.path.join(DYNAMIC_DATA_FOLDER, '*.csv')))
all_engineered_features = []

# 使用tqdm显示处理进度
for file_path in tqdm(dynamic_files, desc="处理患者动态数据"):
    try:
        # 从文件名中提取患者ID
        patient_id = int(os.path.basename(file_path).split('.')[0])
        
        dynamic_df = pd.read_csv(file_path, index_col=0)
        
        # 定义时间窗口
        baseline_window = dynamic_df.loc[-15:-1]
        early_post_window = dynamic_df.loc[0:7]
        
        patient_features = {'PatientID': patient_id}
        
        # 遍历所有动态指标列
        for column in dynamic_df.columns:
            # 分别处理两个时间窗口
            for window_df, prefix in [(baseline_window, 'baseline'), (early_post_window, 'early_post')]:
                series = window_df[column].dropna()
                
                if not series.empty:
                    # 计算聚合统计量
                    patient_features[f'{column}_{prefix}_mean'] = series.mean()
                    patient_features[f'{column}_{prefix}_max'] = series.max()
                    patient_features[f'{column}_{prefix}_min'] = series.min()
                    patient_features[f'{column}_{prefix}_std'] = series.std() if len(series) > 1 else 0
                    patient_features[f'{column}_{prefix}_max_day'] = series.idxmax()
                    
                    # 计算趋势（斜率），至少需要两个点
                    if len(series) >= 2:
                        slope, _, _, _, _ = linregress(series.index, series.values)
                        patient_features[f'{column}_{prefix}_slope'] = slope
                    else:
                        patient_features[f'{column}_{prefix}_slope'] = 0.0 # 单点或无点，无斜率
                else:
                    # 如果窗口内没有数据，填充为NaN
                    for stat in ['mean', 'max', 'min', 'std', 'max_day', 'slope']:
                        patient_features[f'{column}_{prefix}_{stat}'] = np.nan

        all_engineered_features.append(patient_features)
    except Exception as e:
        print(f"处理文件 {file_path} 时发生错误: {e}")

# 将特征列表转换为DataFrame
engineered_features_df = pd.DataFrame(all_engineered_features)
print("动态特征工程完成。")
print(f"共生成 {engineered_features_df.shape[1] - 1} 个动态特征。")

# --- 4. [Step 1.3] 合并静态与动态特征 ---
print("\n步骤 1.3: 合并静态数据与工程化的动态特征...")
# 使用内连接(inner join)确保只保留同时具有静态和动态数据的患者
final_df = pd.merge(static_df, engineered_features_df, on='PatientID', how='inner')
print("数据合并完成。")

# --- 5. 输出最终结果概览 ---
print("\n--- 阶段一完成 ---")
print(f"最终生成的完整特征矩阵维度: {final_df.shape[0]} 位患者, {final_df.shape[1]} 个总特征。")
print("\n前5列预览:")
print(final_df.iloc[:, :5].head())
print("\n最后5列预览 (部分工程化特征):")
print(final_df.iloc[:, -5:].head())

# 建议将结果保存，以便后续阶段使用
output_path = 'final_feature_matrix.csv'
final_df.to_csv(output_path, index=False)
print(f"\n完整特征矩阵已保存至: {output_path}")