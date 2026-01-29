# 预处理Pipeline模板
"""
preprocess.py
-------------
静态与动态特征的预处理 Pipeline。
包括插补、编码与缩放。
"""

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

class StaticDynamicPreprocessor(BaseEstimator, TransformerMixin):
    """
    自定义预处理器，用于统一静态+动态特征的数值/类别处理。
    """
    def __init__(self, num_cols, cat_cols):
        self.num_cols = num_cols
        self.cat_cols = cat_cols
        self.pipeline = None

    def fit(self, X, y=None):
        num_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])
        cat_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse=False))
        ])
        self.pipeline = ColumnTransformer([
            ("num", num_pipe, self.num_cols),
            ("cat", cat_pipe, self.cat_cols)
        ])
        self.pipeline.fit(X)
        return self

    def transform(self, X):
        return self.pipeline.transform(X)