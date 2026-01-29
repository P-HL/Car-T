# SHAP解释模板
"""
shap_explain.py
---------------
利用 SHAP 分析模型特征重要性。
"""

import shap
import joblib
import pandas as pd
import matplotlib.pyplot as plt

def shap_explain(pipeline_path: str, X_train: pd.DataFrame, out_dir: str):
    """
    生成全局 SHAP 特征重要性图。

    Parameters
    ----------
    pipeline_path : str
        模型路径。
    X_train : pd.DataFrame
        训练集特征（用于解释器）。
    out_dir : str
        输出文件夹。
    """
    data = joblib.load(pipeline_path)
    model = data["model"]
    preproc = data["preprocessor"]
    X_proc = preproc.transform(X_train)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_proc)
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_proc, show=False)
    plt.savefig(f"{out_dir}/shap_summary.png", bbox_inches="tight")
    print("✅ SHAP explanation saved.")