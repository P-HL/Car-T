# 数据划分脚本模板
"""
main_split.py
-------------
执行 70/30 外层划分（按 patient_id 分层），生成训练集与测试集。
"""

import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
from pathlib import Path
import yaml

def stratified_patient_split(static_path: str, out_dir: str, test_size: float = 0.3, random_state: int = 42):
    """
    根据患者标签进行分层划分。

    Parameters
    ----------
    static_path : str
        静态数据文件路径。
    out_dir : str
        输出文件夹路径。
    test_size : float
        测试集比例。
    random_state : int
        随机种子。

    Returns
    -------
    None
    """
    df = pd.read_csv(static_path)
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    for train_idx, test_idx in splitter.split(df, df["label"]):
        train_df = df.iloc[train_idx]
        test_df = df.iloc[test_idx]
    
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    train_df.to_csv(f"{out_dir}/train_static.csv", index=False)
    test_df.to_csv(f"{out_dir}/test_static.csv", index=False)

    with open(f"{out_dir}/split_metadata.yaml", "w") as f:
        yaml.safe_dump({
            "test_size": test_size,
            "random_state": random_state,
            "train_size": len(train_df),
            "test_size_abs": len(test_df)
        }, f)

    print(f"✅ Data split complete: {len(train_df)} train / {len(test_df)} test")

if __name__ == "__main__":
    stratified_patient_split("data/static/encoded_standardized.csv", "splits/BNHL_CRS_split_70_30")