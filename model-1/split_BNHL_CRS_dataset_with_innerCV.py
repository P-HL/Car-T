"""
Enhanced split script with 70/30 split + 5-fold internal GroupStratifiedKFold
-------------------------------------------------------------------------------
功能：
1. 主划分：StratifiedShuffleSplit (70% train / 30% test)
2. 内部划分：在训练集上执行5折 GroupStratifiedKFold（近似实现）
3. 每折保存 train/val 病人ID文件
4. 输出元信息 metadata_split.yaml
-------------------------------------------------------------------------------
在split_BNHL_CRS_dataset.py 基础上升级，让它在 训练集 (70%) 内部 再进行 5 折 Group + Stratified 双层交叉验证划分。

🎯 功能目标
升级版脚本实现以下功能：
	1.	先执行 70/30 主划分（保持类别分布一致，患者级独立）；
	2.	再对训练集（70%部分）做 5 折 GroupStratifiedKFold：
	•	保证严重 CRS（label=1）的比例在各折中近似一致；
	•	同时保证同一 patient_id 不出现在不同折；
 	3.	自动输出：
BNHL_CRS_split_70_30/
├── train_static.csv
├── test_static.csv
├── fold_splits/
│    ├── fold1_train_ids.txt
│    ├── fold1_val_ids.txt
│    ├── fold2_train_ids.txt
│    ├── fold2_val_ids.txt
│    └── ...
└── metadata_split.yaml
-------------------------------------------------------------------------------
🧠 背景逻辑
	•	GroupKFold 可确保“同一病人不会出现在不同折”；
	•	StratifiedKFold 保证 label 分布平衡；
	•	sklearn 没有官方 “GroupStratifiedKFold”，但我们可以实现一个简洁可靠的近似版本：
	•	先按 label 分层；
	•	在每个类别中随机分组；
	•	拼合成每折近似平衡的结构。
 
-------------------------------------------------------------------------------
  🗂️ 输出目录结构
 BNHL_CRS_split_70_30/
├── train_static.csv
├── test_static.csv
├── train_ids.txt
├── test_ids.txt
├── fold_splits/
│   ├── fold1_train_ids.txt
│   ├── fold1_val_ids.txt
│   ├── fold2_train_ids.txt
│   ├── fold2_val_ids.txt
│   ├── fold3_train_ids.txt
│   ├── fold3_val_ids.txt
│   ├── fold4_train_ids.txt
│   ├── fold4_val_ids.txt
│   ├── fold5_train_ids.txt
│   └── fold5_val_ids.txt
└── metadata_split.yaml
-------------------------------------------------------------------------------
 📊 典型终端输出示例
 总样本数: 447
0    409
1     38
Name: label, dtype: int64

✅ 主划分完成：
Train: 313 (27 severe CRS)
Test:  134 (11 severe CRS)

🔹 在训练集上创建5折 Group-Stratified CV 划分...
  Fold1: train=251 (pos=22), val=62 (pos=5)
  Fold2: train=250 (pos=21), val=63 (pos=6)
  Fold3: train=250 (pos=22), val=63 (pos=5)
  Fold4: train=252 (pos=22), val=61 (pos=5)
  Fold5: train=249 (pos=21), val=64 (pos=6)
-------------------------------------------------------------------------------
✅ 使用方式
在后续训练脚本（如 train_BNHL_CRS_model.py）中：
	•	读取某个折的 ID 列表，例如：
train_ids = np.loadtxt("BNHL_CRS_split_70_30/fold_splits/fold1_train_ids.txt", dtype=int)
val_ids = np.loadtxt("BNHL_CRS_split_70_30/fold_splits/fold1_val_ids.txt", dtype=int)
	•	在静态表 train_static.csv 里筛选对应 ID 进行训练验证。
-------------------------------------------------------------------------------
⚠️ 注意事项
采样单位：患者级，不可在动态时间片层面打乱
分层策略：通过患者 label 确保正负样本均衡
稀有标签：若正样本太少（<30），建议减少到 3 折以确保每折都有至少 5 个正样本
reproducibility：固定 random_state=42
-------------------------------------------------------------------------------

 
"""

import os
import shutil
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import StratifiedShuffleSplit, StratifiedKFold

# ======================================================
# 1. 用户配置区
# ======================================================
# 静态数据文件路径 - 包含每个患者的静态特征和标签
STATIC_PATH = "/home/phl/PHL/Car-T/data_encoder/output/dataset/encoded_standardized.csv"
# 动态数据目录 - 包含每个患者的时序数据文件（命名格式: {patient_id}.csv）
DYNAMIC_DIR = "/home/phl/PHL/Car-T/data_encoder/output/dataset/processed_standardized"
# 输出目录 - 存放划分后的训练集、测试集和交叉验证折叠文件
OUTPUT_DIR = "./BNHL_CRS_split_70_30"
# 患者ID列名 - 用于标识不同患者的唯一标识符
PATIENT_ID_COL = "patient_id"
# 标签列名 - 0=非严重CRS, 1=严重CRS（目标变量）
LABEL_COL = "label"
# 测试集比例 - 30%的数据用于最终测试
TEST_SIZE = 0.30
# 随机种子 - 确保数据划分的可复现性
RANDOM_STATE = 42
# 交叉验证折数 - 在训练集上执行5折交叉验证
N_FOLDS = 5
# 是否复制动态文件 - True则复制所有患者的动态CSV文件到对应子目录
COPY_DYNAMIC_FILES = True  # 若为True则复制动态文件; 若为 False，将仅生成ID文件，不复制动态CSV

# ======================================================
# 辅助函数：创建Group-Stratified划分
# ======================================================
def group_stratified_kfold(df, group_col, label_col, n_splits=5, random_state=42):
    """
    在患者级别进行分层交叉验证划分。
    
    功能说明:
        实现GroupKFold + StratifiedKFold的组合效果，确保：
        1. 同一患者(group)的所有样本不会跨fold出现
        2. 各fold中正负样本的比例保持近似平衡
    
    实现策略:
        - 先按label将数据分为正样本组和负样本组
        - 分别对两组进行n_splits等分
        - 将对应索引的正负样本组合并作为各fold的验证集
        - 剩余样本作为该fold的训练集
    
    参数:
        df: pandas.DataFrame - 包含患者数据的数据框
        group_col: str - 分组列名（患者ID列），确保同一组不跨fold
        label_col: str - 标签列名，用于分层以保持类别平衡
        n_splits: int - 交叉验证折数，默认5
        random_state: int - 随机种子，确保可复现性
    
    返回:
        list of tuple - 每个元素为 (train_ids, val_ids)，表示一折的训练和验证患者ID数组
                       共返回n_splits个元组
    
    注意事项:
        - 这是sklearn未提供的GroupStratifiedKFold的近似实现
        - 适用于医疗数据等需要患者级独立且类别平衡的场景
        - 当某类样本数不能被n_splits整除时，各fold大小可能略有差异
    """
    # 创建随机数生成器，用于打乱数据顺序
    rng = np.random.RandomState(random_state)
    # 先打乱整个数据框，避免原始数据的排序偏差
    df_shuffled = df.sample(frac=1, random_state=random_state).reset_index(drop=True)

    # 提取label=1（严重CRS）与label=0（非严重CRS）两组患者
    # 分别处理确保各fold都包含足够的正负样本
    pos_df = df_shuffled[df_shuffled[label_col] == 1]
    neg_df = df_shuffled[df_shuffled[label_col] == 0]

    # 将正样本和负样本分别等分成n_splits份
    # np.array_split确保即使不能整除也能合理分配
    pos_groups = np.array_split(pos_df[group_col].values, n_splits)
    neg_groups = np.array_split(neg_df[group_col].values, n_splits)

    # 构建每一折的训练集和验证集ID列表
    folds = []
    for i in range(n_splits):
        # 第i折的验证集：合并第i份正样本和第i份负样本
        val_ids = np.concatenate([pos_groups[i], neg_groups[i]])
        # 第i折的训练集：除验证集外的所有患者ID
        train_ids = df_shuffled[~df_shuffled[group_col].isin(val_ids)][group_col].values
        folds.append((train_ids, val_ids))
    return folds

# ======================================================
# 2. 加载静态数据
# ======================================================
# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)
# 读取静态数据表，包含所有患者的基线特征和CRS标签
print("🔹 Loading static data...")
df = pd.read_csv(STATIC_PATH)

# 验证必需列是否存在 - 确保数据文件包含患者ID和标签列
assert PATIENT_ID_COL in df.columns, f"静态文件中缺少列: {PATIENT_ID_COL}"
assert LABEL_COL in df.columns, f"静态文件中缺少列: {LABEL_COL}"

# 打印数据集基本统计信息
print(f"总样本数: {len(df)}")
# 显示标签分布（0: 非严重CRS, 1: 严重CRS）
print(df[LABEL_COL].value_counts())

# ======================================================
# 3. 分层抽样STRATIFIED SPLIT (患者级别)————主划分 (70/30 StratifiedShuffleSplit)
# ======================================================
# 使用分层抽样进行70/30划分
# - 确保训练集和测试集中严重CRS的比例与总体一致
# - 在患者级别划分，避免同一患者的数据出现在训练集和测试集中
splitter = StratifiedShuffleSplit(
    n_splits=1,              # 只需要一次划分
    test_size=TEST_SIZE,     # 测试集占30%
    random_state=RANDOM_STATE # 固定随机种子确保可复现
)
# split方法的第二个参数传入标签列，实现分层抽样
train_idx, test_idx = next(splitter.split(df, df[LABEL_COL]))

# 根据索引提取训练集和测试集
train_df = df.iloc[train_idx].copy()
test_df = df.iloc[test_idx].copy()

# 提取训练集和测试集的患者ID列表
train_ids = train_df[PATIENT_ID_COL].tolist()
test_ids = test_df[PATIENT_ID_COL].tolist()

# 打印划分统计信息，验证分层效果
print("\n✅ 主划分: 分层抽样完成 (Stratified split complete):")
print(f"Train set: {len(train_df)} patients ({train_df[LABEL_COL].sum()} severe CRS)")
print(f"Test set:  {len(test_df)} patients ({test_df[LABEL_COL].sum()} severe CRS)")

# ======================================================
# 4. CREATE OUTPUT DIRECTORIES & SAVE STATIC DATA
# ======================================================
# 为训练集和测试集的动态数据创建子目录
os.makedirs(os.path.join(OUTPUT_DIR, "train_dynamic"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "test_dynamic"), exist_ok=True)

# ======================================================
# 5. SAVE STATIC CSVs & ID LISTS
# ======================================================
# 保存训练集和测试集的静态数据文件路径
train_static_path = os.path.join(OUTPUT_DIR, "train_static.csv")
test_static_path = os.path.join(OUTPUT_DIR, "test_static.csv")

# 将划分后的静态数据保存为CSV文件
train_df.to_csv(train_static_path, index=False)
test_df.to_csv(test_static_path, index=False)

# 将患者ID列表保存为文本文件，便于后续快速加载
np.savetxt(os.path.join(OUTPUT_DIR, "train_ids.txt"), train_ids, fmt="%s")
np.savetxt(os.path.join(OUTPUT_DIR, "test_ids.txt"), test_ids, fmt="%s")

# ======================================================
# 6. 在训练集上创建内部5折 GroupStratifiedKFold
# ======================================================
# 对训练集进行交叉验证划分，用于模型超参数调优和稳定性评估
print("\n🔹 在训练集上创建5折 Group-Stratified CV 划分...")
# 调用自定义函数进行分组分层交叉验证
folds = group_stratified_kfold(train_df, group_col=PATIENT_ID_COL,
                               label_col=LABEL_COL, n_splits=N_FOLDS,
                               random_state=RANDOM_STATE)

# 创建fold_splits子目录用于存储各折的ID文件
fold_dir = os.path.join(OUTPUT_DIR, "fold_splits")
os.makedirs(fold_dir, exist_ok=True)

# 遍历每一折，保存训练和验证集的患者ID
for i, (train_ids_fold, val_ids_fold) in enumerate(folds, 1):
    # 保存第i折的训练集患者ID
    np.savetxt(os.path.join(fold_dir, f"fold{i}_train_ids.txt"), train_ids_fold, fmt="%s")
    # 保存第i折的验证集患者ID
    np.savetxt(os.path.join(fold_dir, f"fold{i}_val_ids.txt"), val_ids_fold, fmt="%s")

    # 统计当前折中的正样本数量（严重CRS患者数）
    pos_train = train_df[train_df[PATIENT_ID_COL].isin(train_ids_fold)][LABEL_COL].sum()
    pos_val = train_df[train_df[PATIENT_ID_COL].isin(val_ids_fold)][LABEL_COL].sum()
    # 打印当前折的统计信息，用于验证分层效果
    print(f"  Fold{i}: train={len(train_ids_fold)} (pos={pos_train}), "
          f"val={len(val_ids_fold)} (pos={pos_val})")

# ======================================================
# 7. COPY DYNAMIC FILES (OPTIONAL)
# ======================================================
# 如果启用了动态文件复制功能
if COPY_DYNAMIC_FILES:
    print("\n📂 复制动态文件中...")
    # 初始化计数器，用于统计成功复制的文件数量
    n_train_copied, n_test_copied = 0, 0
    # 记录缺失的动态文件ID
    missing_train, missing_test = [], []

    # 复制训练集患者的动态文件
    for pid in train_ids:
        # 构建源文件路径和目标文件路径
        src = os.path.join(DYNAMIC_DIR, f"{pid}.csv")
        dst = os.path.join(OUTPUT_DIR, "train_dynamic", f"{pid}.csv")
        # 检查源文件是否存在
        if os.path.exists(src):
            shutil.copy(src, dst)
            n_train_copied += 1
        else:
            # 记录缺失的文件ID
            missing_train.append(pid)

    # 复制测试集患者的动态文件
    for pid in test_ids:
        src = os.path.join(DYNAMIC_DIR, f"{pid}.csv")
        dst = os.path.join(OUTPUT_DIR, "test_dynamic", f"{pid}.csv")
        if os.path.exists(src):
            shutil.copy(src, dst)
            n_test_copied += 1
        else:
            missing_test.append(pid)

    # 打印复制统计信息
    print(f"动态文件已复制: {n_train_copied} train, {n_test_copied} test")
    # 如果有缺失文件，发出警告
    if missing_train or missing_test:
        print(f"⚠️ 缺失的动态文件:")
        if missing_train:
            print(f"  - 训练集缺失 ({len(missing_train)}): {missing_train[:10]}...")
        if missing_test:
            print(f"  - 测试集缺失 ({len(missing_test)}): {missing_test[:10]}...")

# ======================================================
# 8.保存元信息 GENERATE METADATA YAML
# ======================================================
# 创建元数据字典，记录数据划分的所有关键信息
metadata = {
    "dataset_split": {
        "method": "StratifiedShuffleSplit + GroupStratifiedKFold",  # 划分方法：主划分 + 内部交叉验证
        "test_size": TEST_SIZE,              # 测试集比例
        "n_folds": N_FOLDS,                  # 交叉验证折数
        "random_state": RANDOM_STATE,        # 随机种子
        "total_samples": int(len(df)),       # 总样本数
        "train_samples": int(len(train_df)), # 训练集样本数
        "test_samples": int(len(test_df)),   # 测试集样本数
        "positive_total": int(df[LABEL_COL].sum()),        # 总正样本数（严重CRS）
        "positive_train": int(train_df[LABEL_COL].sum()),  # 训练集正样本数
        "positive_test": int(test_df[LABEL_COL].sum()),    # 测试集正样本数
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 划分时间戳
        "static_input_file": STATIC_PATH,        # 输入静态文件路径
        "dynamic_input_dir": DYNAMIC_DIR,        # 输入动态文件目录
        "train_static_csv": train_static_path,   # 训练集静态文件路径
        "test_static_csv": test_static_path,     # 测试集静态文件路径
        "train_dynamic_dir": os.path.join(OUTPUT_DIR, "train_dynamic"),  # 训练集动态文件目录
        "test_dynamic_dir": os.path.join(OUTPUT_DIR, "test_dynamic"),    # 测试集动态文件目录
    }
}

# 将元数据保存为YAML文件，便于追溯和复现
with open(os.path.join(OUTPUT_DIR, "metadata_split.yaml"), "w") as f:
    yaml.dump(metadata, f, allow_unicode=True)

print(f"\n📄 Metadata written to metadata_split.yaml, 已保存到 {OUTPUT_DIR}")
print("\n🎉 数据划分 + 内部交叉验证折叠文件生成完成！")