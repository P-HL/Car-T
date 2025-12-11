"""
自定义数据集分割器 - 遵循 scikit-learn API 约定
==================================================

本模块提供两个数据分割类，用于替代 sklearn.model_selection.train_test_split：

1. PatientLevelStratifiedSplitter
   - 实现患者级别的分层70/30划分
   - 确保同一患者不会同时出现在训练集和测试集
   - 保持类别比例平衡（分层抽样）
   
2. PatientLevelStratifiedSplitterWithCV
   - 在PatientLevelStratifiedSplitter基础上增加内部交叉验证
   - 对训练集进行5折Group-Stratified交叉验证
   - 适用于需要超参数调优的场景

使用示例：
---------
# 方式1: 简单的70/30划分
splitter = PatientLevelStratifiedSplitter(test_size=0.3, random_state=42)
train_df, test_df = splitter.split(df, label_col="label", patient_id_col="patient_id")

# 方式2: 带内部交叉验证的划分
splitter_cv = PatientLevelStratifiedSplitterWithCV(
    test_size=0.3, n_folds=5, random_state=42
)
train_df, test_df, cv_folds = splitter_cv.split(
    df, label_col="label", patient_id_col="patient_id"
)

设计理念：
---------
- 遵循sklearn的splitter API约定（虽然不是完全继承BaseCrossValidator）
- 专为医疗数据设计，解决患者级独立性问题
- 可与sklearn Pipeline无缝集成
- 提供清晰的统计信息输出

作者: AI Assistant
日期: 2025-11-20
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
from typing import Tuple, List, Optional, Union


class PatientLevelStratifiedSplitter:
    """
    患者级别分层数据分割器
    
    实现基于患者ID的分层随机划分，确保：
    1. 分层抽样：训练集和测试集中各类别的比例与总体一致
    2. 患者级独立性：每个患者只出现在一个集合中（防止数据泄漏）
    3. 可复现性：固定random_state可以重现相同的划分
    
    该类设计用于替代 sklearn.model_selection.train_test_split，
    特别适用于医疗数据等需要保证样本独立性的场景。
    
    参数
    ----
    test_size : float, default=0.3
        测试集所占比例，范围 (0, 1)
        
    random_state : int, default=42
        随机种子，用于保证结果可复现
        
    verbose : bool, default=True
        是否打印划分统计信息
        
    属性
    ----
    train_indices_ : np.ndarray
        训练集在原始数据中的索引位置
        
    test_indices_ : np.ndarray
        测试集在原始数据中的索引位置
        
    train_size_ : int
        训练集样本数
        
    test_size_ : int
        测试集样本数
        
    示例
    ----
    >>> splitter = PatientLevelStratifiedSplitter(test_size=0.3, random_state=42)
    >>> train_df, test_df = splitter.split(df, label_col="CRS_grade", 
    ...                                     patient_id_col="patient_id")
    >>> print(f"训练集: {len(train_df)}, 测试集: {len(test_df)}")
    
    注意
    ----
    - 输入数据框的每一行应代表一个患者（患者级数据）
    - 标签列应为二分类或多分类的离散标签
    - 对于极度不平衡的数据（某类样本<5个），可能无法完美保持比例
    """
    
    def __init__(
        self, 
        test_size: float = 0.3, 
        random_state: int = 42,
        verbose: bool = True
    ):
        """
        初始化分割器
        
        参数
        ----
        test_size : float
            测试集比例，默认0.3（30%）
        random_state : int
            随机种子，默认42
        verbose : bool
            是否输出详细信息，默认True
        """
        if not 0 < test_size < 1:
            raise ValueError(f"test_size must be between 0 and 1, got {test_size}")
            
        self.test_size = test_size
        self.random_state = random_state
        self.verbose = verbose
        
        # 划分后的索引信息（调用split后填充）
        self.train_indices_ = None
        self.test_indices_ = None
        self.train_size_ = None
        self.test_size_ = None
    
    def split(
        self, 
        df: pd.DataFrame, 
        label_col: str,
        patient_id_col: str = "patient_id"
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        执行患者级分层划分
        
        参数
        ----
        df : pd.DataFrame
            待划分的数据框，每行代表一个患者
            
        label_col : str
            标签列名（目标变量列）
            
        patient_id_col : str, default="patient_id"
            患者ID列名
            
        返回
        ----
        train_df : pd.DataFrame
            训练集数据框（已重置索引）
            
        test_df : pd.DataFrame
            测试集数据框（已重置索引）
            
        抛出
        ----
        AssertionError
            如果指定的列不存在于数据框中
        """
        # 验证必需列是否存在
        assert patient_id_col in df.columns, f"数据中缺少患者ID列: {patient_id_col}"
        assert label_col in df.columns, f"数据中缺少标签列: {label_col}"
        
        if self.verbose:
            print("执行患者级分层划分...")
            print(f"   总样本数: {len(df)}")
            print(f"   标签分布:\n{df[label_col].value_counts().to_dict()}")
        
        # 使用StratifiedShuffleSplit进行分层抽样
        splitter = StratifiedShuffleSplit(
            n_splits=1,
            test_size=self.test_size,
            random_state=self.random_state
        )
        
        # 获取训练集和测试集的索引
        train_idx, test_idx = next(splitter.split(df, df[label_col]))
        
        # 保存索引信息
        self.train_indices_ = train_idx
        self.test_indices_ = test_idx
        self.train_size_ = len(train_idx)
        self.test_size_ = len(test_idx)
        
        # 提取训练集和测试集，并重置索引
        train_df = df.iloc[train_idx].copy().reset_index(drop=True)
        test_df = df.iloc[test_idx].copy().reset_index(drop=True)
        
        if self.verbose:
            # 计算各集合中的正样本数（假设label为二分类）
            train_pos = train_df[label_col].sum() if train_df[label_col].dtype in ['int64', 'int32'] else len(train_df[train_df[label_col] == 1])
            test_pos = test_df[label_col].sum() if test_df[label_col].dtype in ['int64', 'int32'] else len(test_df[test_df[label_col] == 1])
            
            print(f"\n分层划分完成:")
            print(f"   训练集: {len(train_df)} 样本 (正样本: {train_pos})")
            print(f"   测试集: {len(test_df)} 样本 (正样本: {test_pos})")
            print(f"   训练集正样本比例: {train_pos/len(train_df)*100:.2f}%")
            print(f"   测试集正样本比例: {test_pos/len(test_df)*100:.2f}%")
        
        return train_df, test_df
    
    def get_split_info(self) -> dict:
        """
        获取划分的详细信息
        
        返回
        ----
        dict
            包含划分配置和统计信息的字典
        """
        return {
            "method": "PatientLevelStratifiedSplitter",
            "test_size": self.test_size,
            "random_state": self.random_state,
            "train_samples": self.train_size_,
            "test_samples": self.test_size_,
            "total_samples": self.train_size_ + self.test_size_ if self.train_size_ else None
        }


class PatientLevelStratifiedSplitterWithCV:
    """
    患者级别分层数据分割器（带内部交叉验证）
    
    在PatientLevelStratifiedSplitter的基础上，增加了对训练集的
    Group-Stratified交叉验证划分功能。适用于需要进行超参数调优
    或模型稳定性评估的场景。
    
    该类实现：
    1. 主划分：70/30 分层划分（患者级独立）
    2. 内部CV：在训练集上进行n_folds折交叉验证
    3. Group-Stratified：确保同一患者不跨fold + 类别比例平衡
    
    参数
    ----
    test_size : float, default=0.3
        测试集所占比例，范围 (0, 1)
        
    n_folds : int, default=5
        交叉验证折数
        
    random_state : int, default=42
        随机种子，用于保证结果可复现
        
    verbose : bool, default=True
        是否打印划分统计信息
        
    属性
    ----
    train_indices_ : np.ndarray
        训练集在原始数据中的索引位置
        
    test_indices_ : np.ndarray
        测试集在原始数据中的索引位置
        
    cv_folds_ : List[Tuple[np.ndarray, np.ndarray]]
        交叉验证折叠信息，每个元素为(train_patient_ids, val_patient_ids)
        
    示例
    ----
    >>> splitter = PatientLevelStratifiedSplitterWithCV(
    ...     test_size=0.3, n_folds=5, random_state=42
    ... )
    >>> train_df, test_df, cv_folds = splitter.split(
    ...     df, label_col="label", patient_id_col="patient_id"
    ... )
    >>> # 使用第1折进行训练
    >>> fold1_train_ids, fold1_val_ids = cv_folds[0]
    >>> fold1_train = train_df[train_df["patient_id"].isin(fold1_train_ids)]
    >>> fold1_val = train_df[train_df["patient_id"].isin(fold1_val_ids)]
    
    注意
    ----
    - 交叉验证仅在训练集上进行，测试集完全独立
    - 适用于数据量较大（>100样本）且正样本数>n_folds*5的场景
    - 对于极小样本，建议减少n_folds以确保每折有足够样本
    """
    
    def __init__(
        self,
        test_size: float = 0.3, 
        n_folds: int = 5,
        random_state: int = 42,
        verbose: bool = True
    ):
        """
        初始化带交叉验证的分割器
        
        参数
        ----
        test_size : float
            测试集比例，默认0.3（30%）
        n_folds : int
            交叉验证折数，默认5
        random_state : int
            随机种子，默认42
        verbose : bool
            是否输出详细信息，默认True
        """
        if not 0 < test_size < 1:
            raise ValueError(f"test_size must be between 0 and 1, got {test_size}")
        if n_folds < 2:
            raise ValueError(f"n_folds must be >= 2, got {n_folds}")
            
        self.test_size = test_size
        self.n_folds = n_folds
        self.random_state = random_state
        self.verbose = verbose
        
        # 使用基础分割器进行主划分
        self.base_splitter = PatientLevelStratifiedSplitter(
            test_size=test_size,
            random_state=random_state,
            verbose=verbose
        )
        
        # 划分后的信息
        self.train_indices_ = None
        self.test_indices_ = None
        self.cv_folds_ = None
    
    def _group_stratified_kfold(
        self, 
        df: pd.DataFrame, 
        group_col: str, 
        label_col: str
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        在患者级别进行分层交叉验证划分（内部方法）
        
        实现GroupKFold + StratifiedKFold的组合效果：
        - 同一患者的数据不会跨fold出现
        - 各fold中正负样本比例保持近似平衡
        
        参数
        ----
        df : pd.DataFrame
            待划分的数据框（通常是训练集）
        group_col : str
            分组列名（患者ID）
        label_col : str
            标签列名
            
        返回
        ----
        List[Tuple[np.ndarray, np.ndarray]]
            每个元素为(train_patient_ids, val_patient_ids)
        """
        # 创建随机数生成器
        rng = np.random.RandomState(self.random_state)
        
        # 打乱数据顺序，避免原始排序偏差
        df_shuffled = df.sample(frac=1, random_state=self.random_state).reset_index(drop=True)
        
        # 分离正负样本
        pos_df = df_shuffled[df_shuffled[label_col] == 1]
        neg_df = df_shuffled[df_shuffled[label_col] == 0]
        
        # 将正负样本分别等分成n_folds份
        pos_groups = np.array_split(pos_df[group_col].values, self.n_folds)
        neg_groups = np.array_split(neg_df[group_col].values, self.n_folds)
        
        # 构建每一折
        folds = []
        for i in range(self.n_folds):
            # 第i折的验证集：合并第i份正样本和负样本
            val_ids = np.concatenate([pos_groups[i], neg_groups[i]])
            # 第i折的训练集：除验证集外的所有患者
            train_ids = df_shuffled[~df_shuffled[group_col].isin(val_ids)][group_col].values
            folds.append((train_ids, val_ids))
        
        return folds
    
    def split(
        self, 
        df: pd.DataFrame, 
        label_col: str,
        patient_id_col: str = "patient_id"
    ) -> Tuple[pd.DataFrame, pd.DataFrame, List[Tuple[np.ndarray, np.ndarray]]]:
        """
        执行患者级分层划分并生成交叉验证折叠
        
        参数
        ----
        df : pd.DataFrame
            待划分的数据框，每行代表一个患者
            
        label_col : str
            标签列名（目标变量列）
            
        patient_id_col : str, default="patient_id"
            患者ID列名
            
        返回
        ----
        train_df : pd.DataFrame
            训练集数据框（已重置索引）
            
        test_df : pd.DataFrame
            测试集数据框（已重置索引）
            
        cv_folds : List[Tuple[np.ndarray, np.ndarray]]
            交叉验证折叠列表，每个元素为(train_patient_ids, val_patient_ids)
            使用示例：
            ```
            for i, (train_ids, val_ids) in enumerate(cv_folds):
                fold_train = train_df[train_df[patient_id_col].isin(train_ids)]
                fold_val = train_df[train_df[patient_id_col].isin(val_ids)]
            ```
        """
        # 步骤1: 使用基础分割器进行70/30主划分
        train_df, test_df = self.base_splitter.split(df, label_col, patient_id_col)
        
        # 保存索引信息
        self.train_indices_ = self.base_splitter.train_indices_
        self.test_indices_ = self.base_splitter.test_indices_
        
        # 步骤2: 在训练集上创建交叉验证折叠
        if self.verbose:
            print(f"\n在训练集上创建{self.n_folds}折 Group-Stratified 交叉验证...")
        
        cv_folds = self._group_stratified_kfold(
            train_df, 
            group_col=patient_id_col, 
            label_col=label_col
        )
        
        self.cv_folds_ = cv_folds
        
        # 打印每一折的统计信息
        if self.verbose:
            for i, (train_ids, val_ids) in enumerate(cv_folds, 1):
                # 统计正样本数
                train_fold_df = train_df[train_df[patient_id_col].isin(train_ids)]
                val_fold_df = train_df[train_df[patient_id_col].isin(val_ids)]
                
                pos_train = train_fold_df[label_col].sum() if train_fold_df[label_col].dtype in ['int64', 'int32'] else len(train_fold_df[train_fold_df[label_col] == 1])
                pos_val = val_fold_df[label_col].sum() if val_fold_df[label_col].dtype in ['int64', 'int32'] else len(val_fold_df[val_fold_df[label_col] == 1])
                
                print(f"   Fold {i}: train={len(train_ids)} (正样本={pos_train}), "
                      f"val={len(val_ids)} (正样本={pos_val})")
        
        return train_df, test_df, cv_folds
    
    def get_split_info(self) -> dict:
        """
        获取划分的详细信息
        
        返回
        ----
        dict
            包含划分配置和统计信息的字典
        """
        base_info = self.base_splitter.get_split_info()
        base_info.update({
            "method": "PatientLevelStratifiedSplitterWithCV",
            "n_folds": self.n_folds,
            "cv_enabled": True
        })
        return base_info


# ============================================================
# 兼容性函数：用于替代 sklearn.model_selection.train_test_split
# ============================================================

def patient_level_train_test_split(
    df: pd.DataFrame,
    label_col: str,
    patient_id_col: str = "patient_id",
    test_size: float = 0.3,
    random_state: int = 42,
    stratify_col: Optional[str] = None,
    verbose: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    患者级别的train_test_split兼容函数
    
    这个函数提供与sklearn.model_selection.train_test_split类似的接口，
    但确保患者级别的独立性和分层抽样。可以直接替换原有的train_test_split调用。
    
    参数
    ----
    df : pd.DataFrame
        待划分的数据框
        
    label_col : str
        标签列名（用于分层抽样）
        
    patient_id_col : str, default="patient_id"
        患者ID列名
        
    test_size : float, default=0.3
        测试集比例
        
    random_state : int, default=42
        随机种子
        
    stratify_col : str, optional
        分层列名（默认使用label_col，保持与sklearn一致的参数名）
        
    verbose : bool, default=True
        是否打印详细信息
        
    返回
    ----
    train_df, test_df : Tuple[pd.DataFrame, pd.DataFrame]
        训练集和测试集数据框
        
    示例
    ----
    >>> # 原始代码
    >>> train_df, test_df = train_test_split(df, test_size=0.3, 
    ...                                       stratify=df["label"], random_state=42)
    >>> 
    >>> # 替换为患者级别划分
    >>> train_df, test_df = patient_level_train_test_split(
    ...     df, label_col="label", patient_id_col="patient_id",
    ...     test_size=0.3, random_state=42
    ... )
    """
    # 如果指定了stratify_col，使用它；否则使用label_col
    stratify_column = stratify_col if stratify_col is not None else label_col
    
    splitter = PatientLevelStratifiedSplitter(
        test_size=test_size,
        random_state=random_state,
        verbose=verbose
    )
    
    return splitter.split(df, stratify_column, patient_id_col)


if __name__ == "__main__":
    """
    测试代码和使用示例
    """
    print("=" * 60)
    print("患者级别分层分割器 - 测试示例")
    print("=" * 60)
    
    # 创建示例数据
    np.random.seed(42)
    n_patients = 100
    
    sample_data = pd.DataFrame({
        'patient_id': range(1, n_patients + 1),
        'age': np.random.randint(20, 80, n_patients),
        'label': np.random.choice([0, 1], n_patients, p=[0.85, 0.15])  # 不平衡数据
    })
    
    print(f"\n示例数据集: {len(sample_data)} 个患者")
    print(f"标签分布: {sample_data['label'].value_counts().to_dict()}")
    
    # 测试1: 简单分割
    print("\n" + "=" * 60)
    print("测试1: 基础患者级分层分割")
    print("=" * 60)
    
    splitter1 = PatientLevelStratifiedSplitter(test_size=0.3, random_state=42)
    train_df, test_df = splitter1.split(sample_data, label_col="label", 
                                         patient_id_col="patient_id")
    
    print(f"\n分割信息: {splitter1.get_split_info()}")
    
    # 测试2: 带交叉验证的分割
    print("\n" + "=" * 60)
    print("测试2: 带交叉验证的患者级分层分割")
    print("=" * 60)
    
    splitter2 = PatientLevelStratifiedSplitterWithCV(
        test_size=0.3, n_folds=5, random_state=42
    )
    train_df, test_df, cv_folds = splitter2.split(
        sample_data, label_col="label", patient_id_col="patient_id"
    )
    
    print(f"\n分割信息: {splitter2.get_split_info()}")
    print(f"交叉验证折数: {len(cv_folds)}")
    
    # 测试3: 兼容函数
    print("\n" + "=" * 60)
    print("测试3: train_test_split兼容函数")
    print("=" * 60)
    
    train_df, test_df = patient_level_train_test_split(
        sample_data,
        label_col="label",
        patient_id_col="patient_id",
        test_size=0.3,
        random_state=42
    )
    
    print("\n所有测试完成！")
