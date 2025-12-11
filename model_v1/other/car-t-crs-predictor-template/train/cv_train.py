# 交叉验证训练模板
"""
cv_train.py
-----------
执行 5 折交叉验证训练 + 随机搜索调参。
"""

from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV
from lightgbm import LGBMClassifier
from sklearn.metrics import average_precision_score
import numpy as np
import pandas as pd
import joblib

def cross_validate_with_search(X, y, folds, param_distributions, n_iter=50, random_state=42):
    """
    执行带交叉验证的随机搜索。

    Parameters
    ----------
    X : np.ndarray or pd.DataFrame
        输入特征。
    y : np.ndarray
        标签。
    folds : int
        折数。
    param_distributions : dict
        参数搜索空间。
    n_iter : int
        随机搜索迭代次数。
    random_state : int
        随机种子。

    Returns
    -------
    best_params : dict
        最优参数。
    """
    model = LGBMClassifier(random_state=random_state)
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=random_state)
    search = RandomizedSearchCV(
        model,
        param_distributions=param_distributions,
        n_iter=n_iter,
        scoring="average_precision",
        cv=cv,
        n_jobs=-1,
        verbose=1,
        random_state=random_state
    )
    search.fit(X, y)
    print(f"Best AUPRC: {search.best_score_:.3f}")
    print("Best params:", search.best_params_)
    joblib.dump(search.best_params_, "artifacts/best_params.pkl")
    return search.best_params_