"""
把 447 位患者 按比例 70% 训练集 / 30% 测试集划分，
同时保证以下三点：
	1.	分层抽样：严重 CRS (=1) 和 非严重 CRS (=0) 的比例在训练集与测试集基本一致；
	2.	患者级独立性：每个 patient_id 只出现在一个集合中（防止动态片段泄漏）；
	3.	可复现：固定 random_state，生成对应 metadata 与 ID 文件。
 ---------------------------------------------------------------
总样本数447
CRS=1 (高毒)：38 (≈ 8.5%)
CRS=0 (低毒/无毒)：409 (≈ 91.5%)

分层划分目标：
训练集约 313 例（其中 ≈ 27–28 例 CRS=1）；
测试集约 134 例（其中 ≈ 10–11 例 CRS=1）。
Enhanced dataset split script for B-NHL CRS binary classification
---------------------------------------------------------------
使用一种混合方法：
	•	分层抽样（StratifiedShuffleSplit） 来保持类别比例；
	•	患者级划分（每个病人唯一 ID）；
	•	生成：train_ids.txt、test_ids.txt、metadata_split.yaml；
	•	保留原始 CSV 不动，仅保存 ID 列表，便于后续 Pipeline 按 ID 筛选。
---------------------------------------------------------------
额外说明与扩展建议
1. 防止时间泄漏
如果你的动态数据中每位病人记录到 +30 天，为保证未来预测不泄漏“未来信息”，
请确保在生成 patient_feature_table.csv 时，只使用 Day ≤ +2 的数据。
---------------------------------------------------------------
2. 交叉验证拓展
你也可以在训练集上再做 5 折 GroupStratifiedKFold 进行内部验证：
from sklearn.model_selection import StratifiedKFold
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for tr_idx, val_idx in skf.split(train_df, train_df[LABEL_COL]):
    # 每折独立训练验证
---------------------------------------------------------------
3. 类别不平衡
严重 CRS 约 8.5% → 属于中度不平衡：
	•	使用 scale_pos_weight = neg/pos （LightGBM 参数）
	•	评估时优先报告 AUPRC 与 敏感度@特异度=0.9
---------------------------------------------------------------
4.可追溯性
在论文或报告中，你可以直接引用：
Data split: StratifiedShuffleSplit (70% train / 30% test, random_state=42)
Positive rate: 8.5% overall, preserved in both subsets
---------------------------------------------------------------
- Stratified 70/30 split by CRS label
- Patient-level unique split
- Copies per-patient dynamic CSV files into train/test subfolders
- Exports static CSVs (train/test)
- Generates reproducible metadata YAML
---------------------------------------------------------------
- 按 CRS 标签进行 70/30 分层
	•	自动识别并加载你的静态文件和动态文件夹；
	•	将动态文件（每位患者一个 CSV）按划分结果复制到两个新文件夹（train_dynamic/、test_dynamic/）；
	•	同步生成静态表的 train_static.csv 和 test_static.csv；
	•	保存所有划分信息到 metadata_split.yaml；
	•	确保随机种子固定、类别比例一致、患者级独立，生成可复现的元数据 YAML 文件；
	•	结构清晰、可直接运行在你的数据路径上。

执行后目录结构如下：
BNHL_CRS_split_70_30/
├── train_static.csv           # 训练集静态数据
├── test_static.csv            # 测试集静态数据
├── train_ids.txt              # 训练集患者ID
├── test_ids.txt               # 测试集患者ID
├── train_dynamic/             # 各病人的动态CSV
│    ├── 1.csv
│    ├── 2.csv
│    └── ...
├── test_dynamic/
│    ├── 12.csv
│    ├── 37.csv
│    └── ...
└── metadata_split.yaml
metadata_split.yaml 中会保存当前划分的统计与随机种子，保证你未来能复现同一划分。
---------------------------------------------------------------
执行后你能立即做的事
训练模型：train_static.csv, train_dynamic/作为 Pipeline 的训练输入
验证模型：test_static.csv, test_dynamic/用于最终性能评估
溯源：metadata_split.yaml包含随机种子、比例、日期，确保可复现
---------------------------------------------------------------
附加建议
样本单位：保持“每病人一例”一致，防止跨病人动态信息泄漏
动态时间窗：仅保留 Day ≤ +2 的动态特征用于训练
类别不平衡：LightGBM 中设置 scale_pos_weight = neg/pos
交叉验证：仅在 train_static.csv 上做 5-fold GroupStratifiedKFold
测试集：绝对不参与任何插补或特征选择拟合
---------------------------------------------------------------

"""

import os
import shutil
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import StratifiedShuffleSplit

# ======================================================
# 1. 用户配置区
# ======================================================
# 静态数据文件路径 - 包含每个患者的静态特征和标签
STATIC_PATH = "/home/phl/PHL/Car-T/disease_partition/output/B-NHL_reindexed/csv/B-NHL_static_data_example.csv"
# 动态数据目录 - 包含每个患者的时序数据文件（命名格式: {patient_id}.csv）
DYNAMIC_DIR = "/home/phl/PHL/Car-T/disease_partition/output/B-NHL_reindexed/processed"
# 输出目录 - 存放划分后的训练集和测试集
OUTPUT_DIR = "./output/datasets/BNHL_CRS_split_70_30"
# 患者ID列名 - 用于标识不同患者的唯一标识符（对应静态数据中的ID列）
PATIENT_ID_COL = "ID"
# 标签列名 - 0=非严重CRS, 1=严重CRS（目标变量
LABEL_COL = "CRS_grade"
# 测试集比例 - 30%的数据用于最终测试
TEST_SIZE = 0.30
# 随机种子 - 确保数据划分的可复现性
RANDOM_STATE = 42
# 是否复制动态文件 - True则复制所有患者的动态CSV文件到对应子目录
COPY_DYNAMIC_FILES = True  # 若为True则复制动态文件; 若为 False，将仅生成ID文件，不复制动态CSV

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
# 3. 分层抽样STRATIFIED SPLIT (患者级别)
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

# 根据索引提取训练集和测试集，并重置索引
train_df = df.iloc[train_idx].copy().reset_index(drop=True)
test_df = df.iloc[test_idx].copy().reset_index(drop=True)

# 提取训练集和测试集的患者ID列表
train_ids = train_df[PATIENT_ID_COL].tolist()
test_ids = test_df[PATIENT_ID_COL].tolist()

# 打印划分统计信息，验证分层效果
print("\n✅ 分层抽样完成 (Stratified split complete):")
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
# 6. COPY DYNAMIC FILES (OPTIONAL)
# ======================================================
# 如果启用了动态文件复制功能
if COPY_DYNAMIC_FILES:
    print("\n📂 Copying dynamic files...")
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
# 7.保存元信息 GENERATE METADATA YAML
# ======================================================
# 创建元数据字典，记录数据划分的所有关键信息
metadata = {
    "dataset_split": {
        "method": "StratifiedShuffleSplit",  # 划分方法
        "test_size": TEST_SIZE,              # 测试集比例
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

# ======================================================
# 8. SUMMARY
# ======================================================
def ratio_info(df_input, name):
    """
    计算并格式化数据集的类别比例信息
    
    参数:
        df_input: pandas.DataFrame - 数据框
        name: str - 数据集名称（如"Train"或"Test"）
    
    返回:
        str - 格式化的比例信息字符串
    """
    total = len(df_input)                 # 总样本数
    pos = df_input[LABEL_COL].sum()      # 正样本数（严重CRS）
    ratio = pos / total * 100             # 正样本比例
    return f"{name}: {pos}/{total} = {ratio:.2f}% positive"

# 打印类别平衡总结
print("\n📊 类别平衡总结:")
print(ratio_info(train_df, "Train"))
print(ratio_info(test_df, "Test"))

print(f"\n🎉 数据划分完成！结果已保存到: {OUTPUT_DIR}")