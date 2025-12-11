"""
perfect_pipeline.py
--------------------
完美无泄漏（NO-LEAK）静态 + 动态特征工程 Pipeline 模板

功能：
1. 删除常量列（适用于 disease 这种筛选后全为 B-NHL 的列）
2. 标签二元化（如毒性等级 <=2 = 0；>2 = 1）
3. 静态特征编码：
    - 数值特征：中位数插补 + 标准化
    - 类别特征（无序）：OneHot 编码
    - 序数特征（有序）：Ordinal 编码
4. 动态特征工程：
    - Day -15 ~ +2 数据聚合 (动态 CSV → 统计特征)
    - 只在训练集上拟合插补等统计特征
5. 最终 sklearn Pipeline：保证无泄漏
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from scipy.stats import linregress
from scipy.integrate import trapezoid
import os


# ============================================================
# 1. 删除常量列
# ============================================================

class ConstantColumnDropper(BaseEstimator, TransformerMixin):
    """
    删除数据集中所有值都相同的列（常量列）
    
    功能说明:
        在数据预处理阶段自动识别并删除常量列（如经过疾病筛选后，所有样本的
        disease列都是"B-NHL"）。这些列对模型训练没有任何贡献，删除可以：
        - 减少特征维度，提高训练效率
        - 避免某些算法的数值问题
        - 使特征集更简洁
    
    使用场景:
        - 在数据拆分之前使用，确保训练集和测试集使用相同的特征集
        - 特别适用于经过条件筛选后的医疗数据（如单一疾病类型）
    
    实现逻辑:
        1. fit阶段：在训练集上识别唯一值数量≤1的列（常量列）
        2. transform阶段：删除这些列（训练集和测试集都应用相同的删除规则）
        3. 防止数据泄漏：只使用训练集的统计信息，测试集不影响决策
    
    参数:
        无
    
    属性:
        constant_cols_ (list): fit后存储识别出的常量列名列表
    
    示例:
        >>> dropper = ConstantColumnDropper()
        >>> X_train_cleaned = dropper.fit_transform(X_train)
        >>> X_test_cleaned = dropper.transform(X_test)
        >>> print(f"删除了 {len(dropper.constant_cols_)} 个常量列: {dropper.constant_cols_}")
    """

    def __init__(self):
        """初始化常量列删除器"""
        self.constant_cols_ = []

    def fit(self, X, y=None):
        """
        在训练集上识别常量列
        
        参数:
            X (pd.DataFrame): 输入数据框
            y (array-like, optional): 目标变量（未使用）
        
        返回:
            self: 返回自身以支持链式调用
        """
        # 识别唯一值数量≤1的列（即所有值都相同或全为缺失值的列）
        self.constant_cols_ = [col for col in X.columns if X[col].nunique() <= 1]
        
        # 打印识别结果，便于调试和验证
        if self.constant_cols_:
            print(f"[ConstantColumnDropper] 识别到 {len(self.constant_cols_)} 个常量列: {self.constant_cols_}")
        else:
            print(f"[ConstantColumnDropper] 未发现常量列")
        
        return self

    def transform(self, X):
        """
        删除识别出的常量列
        
        参数:
            X (pd.DataFrame): 输入数据框
        
        返回:
            pd.DataFrame: 删除常量列后的数据框
        """
        # 使用 errors="ignore" 避免列不存在时报错（兼容性处理）
        return X.drop(columns=self.constant_cols_, errors="ignore")


# ============================================================
# 2. 毒性二元化转换器
# ============================================================

class ToxicityBinarizer(BaseEstimator, TransformerMixin):
    """
    将一个或多个毒性等级列转换为二元分类标签
    
    功能说明:
        将多分类的毒性等级（如CRS等级：0-5级）转换为二元分类问题：
        - 非严重/轻度（≤threshold级）→ 0  [包含threshold值]
        - 严重（>threshold级）→ 1        [不包含threshold值]
        
        例如：threshold=2时
            - 等级0, 1, 2 → 0 (非严重)
            - 等级3, 4, 5 → 1 (严重)
        
        这种二元化策略常用于医疗预测任务，将重点放在识别严重病例上。
        
        **增强功能**: 支持同时处理多个毒性指标，每个指标可以有独立的阈值。
    
    使用场景:
        - Car-T细胞疗法的CRS（细胞因子释放综合征）严重程度预测
        - ICANS（免疫效应细胞相关神经毒性综合征）分级预测
        - 同时处理多种毒性反应（CRS、ICANS、感染等）
        - 其他需要将多级毒性反应简化为二元结果的场景
    
    实现逻辑:
        1. 检查指定的毒性等级列是否存在
        2. 应用二元化规则：grade > threshold → 1, 否则 → 0
        3. 返回转换后的数据框（保留其他所有列不变）
    
    参数:
        columns (str, list, or dict): 待转换的列配置
            - str: 单个列名（使用默认阈值2）
            - list: 多个列名列表（所有列使用相同的threshold参数）
            - dict: {列名: 阈值} 映射，每个列可以有不同的阈值
            示例:
                - "CRS_grade"  # 单列，阈值=2
                - ["CRS", "ICANS"]  # 多列，都用阈值=2
                - {"CRS": 2, "ICANS": 1, "Infection": 3}  # 多列，各自阈值
        
        threshold (int): 默认二元化阈值，默认为2
                        - ≤threshold → 0（非严重，包含等于threshold的情况）
                        - >threshold → 1（严重，不包含等于threshold的情况）
                        例如：threshold=2时，等级2算作非严重(0)
                        仅在columns为str或list时使用
        
        suffix (str, optional): 添加到转换后列名的后缀，默认None（覆盖原列）
                               例如: suffix="_binary" 会将 "CRS" 转为 "CRS_binary"
    
    属性:
        columns_config (dict): 存储每个列及其对应阈值的字典
        suffix (str): 列名后缀
    
    示例:
        >>> # 用法1: 单列转换（向后兼容）
        >>> binarizer = ToxicityBinarizer(columns="CRS_grade", threshold=2)
        >>> X_transformed = binarizer.fit_transform(X)
        >>> 
        >>> # 用法2: 多列转换，相同阈值
        >>> binarizer = ToxicityBinarizer(columns=["CRS", "ICANS"], threshold=2)
        >>> X_transformed = binarizer.fit_transform(X)
        >>> 
        >>> # 用法3: 多列转换，不同阈值（推荐）
        >>> binarizer = ToxicityBinarizer(columns={
        ...     "CRS": 2,      # CRS等级：≤2轻度，>2严重
        ...     "ICANS": 1,    # ICANS等级：≤1轻度，>1严重
        ...     "Infection": 3 # 感染等级：≤3轻度，>3严重
        ... })
        >>> X_transformed = binarizer.fit_transform(X)
        >>> 
        >>> # 用法4: 创建新列而不覆盖原列
        >>> binarizer = ToxicityBinarizer(
        ...     columns={"CRS": 2, "ICANS": 1},
        ...     suffix="_binary"
        ... )
        >>> X_transformed = binarizer.fit_transform(X)
        >>> # 结果包含: CRS, CRS_binary, ICANS, ICANS_binary
    
    注意事项:
        - 输入列的值应该是数值型（整数或浮点数）
        - 如果列不存在，会抛出清晰的错误提示
        - 缺失值（NaN）会被保留为NaN，不会被强制转换
        - 支持向后兼容：可以像之前一样使用单列模式
    """

    def __init__(self, columns="CRS_grade", threshold=2, suffix=None):
        """
        初始化毒性二元化转换器
        
        参数:
            columns (str, list, or dict): 列配置（单列/多列/带阈值字典）
            threshold (int): 默认阈值，默认2
            suffix (str, optional): 列名后缀，默认None（覆盖原列）
        """
        # 标准化列配置为字典格式
        if isinstance(columns, str):
            # 单列字符串 -> {列名: 阈值}
            self.columns_config = {columns: threshold}
        elif isinstance(columns, list):
            # 列表 -> {列名: 默认阈值}
            self.columns_config = {col: threshold for col in columns}
        elif isinstance(columns, dict):
            # 已经是字典，直接使用
            self.columns_config = columns
        else:
            raise TypeError(
                f"[ToxicityBinarizer] 错误：columns 参数类型不支持。"
                f"应该是 str、list 或 dict，当前类型为 {type(columns)}"
            )
        
        self.suffix = suffix
        
        # 保留原始参数（用于sklearn兼容性）
        self.columns = columns
        self.threshold = threshold

    def fit(self, X, y=None):
        """
        拟合方法（验证列存在性和数据类型）
        
        参数:
            X (pd.DataFrame): 输入数据框
            y (array-like, optional): 目标变量（未使用）
        
        返回:
            self: 返回自身以支持链式调用
        """
        print(f"[ToxicityBinarizer] 配置: 处理 {len(self.columns_config)} 个毒性指标")
        
        # 验证每个列
        for col, thresh in self.columns_config.items():
            # 验证列是否存在
            if col not in X.columns:
                raise ValueError(
                    f"[ToxicityBinarizer] 错误：列 '{col}' 不存在于数据框中。"
                    f"可用列: {list(X.columns)}"
                )
            
            # 验证列是否为数值型
            if not pd.api.types.is_numeric_dtype(X[col]):
                raise TypeError(
                    f"[ToxicityBinarizer] 错误：列 '{col}' 必须是数值类型，"
                    f"当前类型为 {X[col].dtype}"
                )
            
            # 打印每个列的配置（明确边界值处理）
            print(f"  [{col}] 阈值={thresh}, 规则: ≤{thresh} → 0 (非严重，包含{thresh}), >{thresh} → 1 (严重)")
            
            # 打印原始分布
            value_counts = X[col].value_counts().sort_index()
            print(f"    原始分布: {value_counts.to_dict()}")
        
        return self

    def transform(self, X):
        """
        应用二元化转换到所有指定的列
        
        参数:
            X (pd.DataFrame): 输入数据框
        
        返回:
            pd.DataFrame: 转换后的数据框
        """
        # 创建副本以避免修改原始数据
        X = X.copy()
        
        print(f"\n[ToxicityBinarizer] 开始转换 {len(self.columns_config)} 个列...")
        
        # 对每个列应用二元化
        for col, thresh in self.columns_config.items():
            # 确定目标列名
            if self.suffix is not None:
                target_col = f"{col}{self.suffix}"
            else:
                target_col = col
            
            # 应用二元化规则：
            # - 如果 grade > threshold: 返回 1 (严重)
            # - 如果 grade <= threshold: 返回 0 (非严重)
            # - 如果 grade 是 NaN: 保持 NaN (缺失值)
            # 
            # 示例（threshold=2）:
            #   原始值: [0, 1, 2, 3, 4, NaN]
            #   结果:   [0, 0, 0, 1, 1, NaN]
            binary_result = (X[col] > thresh).astype(float)
            
            # 将NaN位置恢复为NaN（保留缺失值，不强制转换）
            X[target_col] = binary_result.where(X[col].notna(), np.nan).astype('Int64')
            
            # 打印转换结果（详细显示各类样本数）
            binary_counts = X[target_col].value_counts().sort_index()
            n_missing = X[target_col].isna().sum()
            
            print(f"  [{col} → {target_col}] 转换完成:")
            print(f"    0 (≤{thresh}级，非严重): {binary_counts.get(0, 0)} 样本")
            print(f"    1 (>{thresh}级，严重): {binary_counts.get(1, 0)} 样本")
            if n_missing > 0:
                print(f"    NaN (缺失值): {n_missing} 样本")
        
        print(f"[ToxicityBinarizer] 所有列转换完成 ✓\n")
        
        return X


# ============================================================
# 3. 动态特征聚合器（核心）
# ============================================================

class DynamicFeatureAggregator(BaseEstimator, TransformerMixin):
    """
    对动态时间序列进行特征聚合。
    输入：static_df["patient_id"]
    对每个 patient_id 加载对应 dynamic CSV。
    
    输出：动态特征（均值/方差/最大/最小/斜率/AUC）
    """

    def __init__(self, dynamic_dir, obs_start=-15, obs_end=2):
        self.dynamic_dir = dynamic_dir
        self.obs_start = obs_start
        self.obs_end = obs_end
        self.feature_names_ = None

    def _extract_features(self, csv_path):
        df = pd.read_csv(csv_path)
        if "Day" not in df.columns:
            df.rename(columns={df.columns[0]: "Day"}, inplace=True)

        df = df[(df["Day"] >= self.obs_start) & (df["Day"] <= self.obs_end)]
        
        out = {}
        for col in df.columns:
            if col == "Day":
                continue

            series = df[col].astype(float)

            out[f"{col}_mean"] = series.mean()
            out[f"{col}_std"] = series.std()
            out[f"{col}_min"] = series.min()
            out[f"{col}_max"] = series.max()

            # AUC
            try:
                out[f"{col}_auc"] = trapezoid(series.fillna(method='ffill').fillna(0),
                                              df["Day"])
            except:
                out[f"{col}_auc"] = np.nan

            # slope
            try:
                slope, _, _, _, _ = linregress(df["Day"], series)
                out[f"{col}_slope"] = slope
            except:
                out[f"{col}_slope"] = np.nan

        return out

    def fit(self, X, y=None):
        # 先扫描一个样本以获取 feature_names
        pid = X["patient_id"].iloc[0]
        csv_path = os.path.join(self.dynamic_dir, f"{pid}.csv")
        sample_features = self._extract_features(csv_path)

        self.feature_names_ = list(sample_features.keys())
        return self

    def transform(self, X):
        results = []
        for pid in X["patient_id"]:
            csv_path = os.path.join(self.dynamic_dir, f"{pid}.csv")

            if not os.path.exists(csv_path):
                # 缺失动态文件 → 全 NaN
                row = {col: np.nan for col in self.feature_names_}
            else:
                row = self._extract_features(csv_path)

            results.append(row)

        return pd.DataFrame(results)[self.feature_names_]


# ============================================================
# 4. 主预处理器（静态 + 动态）
# ============================================================

class FullPreprocessor(BaseEstimator, TransformerMixin):
    """
    将静态特征预处理 + 动态特征聚合整合为一个 sklearn transformer。
    """

    def __init__(self, numeric_cols, categorical_cols, ordinal_cols, dynamic_dir):
        self.numeric_cols = numeric_cols
        self.categorical_cols = categorical_cols
        self.ordinal_cols = ordinal_cols
        self.dynamic_dir = dynamic_dir

        # 组件
        self.constant_dropper = ConstantColumnDropper()
        self.dynamic_agg = DynamicFeatureAggregator(dynamic_dir)

        # 静态预处理
        self.static_transformer = ColumnTransformer(
            transformers=[
                ("num", Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler())
                ]), numeric_cols),

                ("cat", Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore"))
                ]), categorical_cols),

                ("ord", Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("ordinal", OrdinalEncoder())
                ]), ordinal_cols)
            ]
        )

        self.fitted_ = False

    def fit(self, X, y=None):
        # 1. 删除常量列
        X = self.constant_dropper.fit_transform(X)

        # 2. 动态特征：fit 时收集特征结构
        dyn = self.dynamic_agg.fit_transform(X)

        # 3. 静态特征
        self.static_transformer.fit(X, y)

        self.fitted_ = True
        return self

    def transform(self, X):
        assert self.fitted_, "Must call fit() before transform()"

        # 常量列删除
        Xc = self.constant_dropper.transform(X)

        # 静态
        X_static = self.static_transformer.transform(Xc)

        # 动态
        X_dyn = self.dynamic_agg.transform(Xc).to_numpy()

        # 拼接静态 + 动态
        return np.hstack([X_static, X_dyn])


# ============================================================
# 5. 最终构造模型 Pipeline
# ============================================================

from lightgbm import LGBMClassifier


def build_no_leak_pipeline(numeric_cols, categorical_cols, ordinal_cols, dynamic_dir):
    """
    构建一个包含：
        - 完整预处理器
        - LightGBM 模型
    的 sklearn Pipeline。
    """
    preproc = FullPreprocessor(
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
        ordinal_cols=ordinal_cols,
        dynamic_dir=dynamic_dir
    )

    model = LGBMClassifier(
        random_state=42,
        n_estimators=500,
        learning_rate=0.03,
        class_weight="balanced"
    )

    pipe = Pipeline([
        ("preprocessor", preproc),
        ("model", model)
    ])

    return pipe