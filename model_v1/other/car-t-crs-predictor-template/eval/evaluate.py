# 测试评估模板
"""
evaluate.py
------------
在独立测试集上评估最终模型。
"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, precision_score, recall_score, brier_score_loss
import joblib

def evaluate_on_test(pipeline_path: str, X_test: pd.DataFrame, y_test: np.ndarray):
    """
    加载模型并在测试集上评估性能。

    Parameters
    ----------
    pipeline_path : str
        模型文件路径。
    X_test : pd.DataFrame
        测试集特征。
    y_test : np.ndarray
        测试集标签。

    Returns
    -------
    dict
        指标字典。
    """
    pipe = joblib.load(pipeline_path)
    probs = pipe["model"].predict_proba(pipe["preprocessor"].transform(X_test))[:, 1]
    preds = (probs >= 0.5).astype(int)

    metrics = {
        "ROC_AUC": roc_auc_score(y_test, probs),
        "AUPRC": average_precision_score(y_test, probs),
        "F1": f1_score(y_test, preds),
        "Precision": precision_score(y_test, preds),
        "Recall": recall_score(y_test, preds),
        "Brier": brier_score_loss(y_test, probs)
    }

    pd.DataFrame([metrics]).to_csv("artifacts/test_metrics.csv", index=False)
    print("✅ Evaluation complete:", metrics)
    return metrics