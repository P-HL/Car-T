# 动态聚合函数模板
"""
aggregation.py
---------------
动态特征聚合：将每位患者的时间序列数据（Day -15 ~ +2）
转换为一组统计特征，用于模型输入。
"""

import pandas as pd
import numpy as np
from scipy.stats import linregress
from scipy.integrate import trapezoid

def aggregate_dynamic(csv_path: str, obs_start: int, obs_end: int) -> dict:
    """
    对单个病人的动态数据进行聚合。

    Parameters
    ----------
    csv_path : str
        病人动态CSV路径。
    obs_start : int
        观察窗口起始天数。
    obs_end : int
        观察窗口结束天数。

    Returns
    -------
    dict
        动态聚合特征字典。
    """
    df = pd.read_csv(csv_path)
    if "Day" not in df.columns:
        df.rename(columns={df.columns[0]: "Day"}, inplace=True)
    df = df[(df["Day"] >= obs_start) & (df["Day"] <= obs_end)]
    features = {}
    for col in df.columns:
        if col == "Day": continue
        series = df[col].dropna()
        if series.empty:
            features[f"{col}_mean"] = np.nan
            continue
        features[f"{col}_mean"] = np.nanmean(series)
        features[f"{col}_std"] = np.nanstd(series)
        features[f"{col}_max"] = np.nanmax(series)
        features[f"{col}_min"] = np.nanmin(series)
        features[f"{col}_auc"] = trapezoid(series, df["Day"].iloc[:len(series)])
        if len(series) > 1:
            slope, *_ = linregress(df["Day"].iloc[:len(series)], series)
            features[f"{col}_slope"] = slope
    return features