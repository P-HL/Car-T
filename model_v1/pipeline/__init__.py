"""
Pipeline 模块
============

这个包提供了用于 Car-T 细胞疗法数据处理和建模的完整 Pipeline 工具集。

主要功能模块：
-----------
1. perfect_pipeline - 数据预处理和特征工程
2. data_splitters - 患者级别分层数据分割

使用示例：
---------
>>> from pipeline import ToxicityBinarizer, ConstantColumnDropper
>>> from pipeline import PatientLevelStratifiedSplitter
>>> 
>>> # 数据预处理
>>> dropper = ConstantColumnDropper()
>>> df_cleaned = dropper.fit_transform(df)
>>> 
>>> binarizer = ToxicityBinarizer(columns=["CRS", "ICANS"], threshold=2)
>>> df_final = binarizer.fit_transform(df_cleaned)
>>> 
>>> # 数据分割
>>> splitter = PatientLevelStratifiedSplitter(test_size=0.3, random_state=42)
>>> train_df, test_df = splitter.split(df_final, label_col="CRS", patient_id_col="ID")

作者: AI Assistant
版本: 1.0.0
日期: 2025-11-21
"""

# ============================================================
# 从 perfect_pipeline 模块导入预处理类
# ============================================================

from .perfect_pipeline import (
    # 数据清理和转换
    ConstantColumnDropper,
    ToxicityBinarizer,
    
    # 动态特征处理
    DynamicFeatureAggregator,
    
    # 完整预处理器
    FullPreprocessor,
    
    # Pipeline 构建函数
    build_no_leak_pipeline,
)

# ============================================================
# 从 data_splitters 模块导入数据分割类
# ============================================================

from .data_splitters import (
    # 分割器类
    PatientLevelStratifiedSplitter,
    PatientLevelStratifiedSplitterWithCV,
    
    # 兼容函数
    patient_level_train_test_split,
)


# ============================================================
# 定义公开的 API
# ============================================================

__all__ = [
    # perfect_pipeline 导出
    'ConstantColumnDropper',
    'ToxicityBinarizer',
    'DynamicFeatureAggregator',
    'FullPreprocessor',
    'build_no_leak_pipeline',
    
    # data_splitters 导出
    'PatientLevelStratifiedSplitter',
    'PatientLevelStratifiedSplitterWithCV',
    'patient_level_train_test_split',
]

# 模块级文档
__doc__ = """
Pipeline 工具包 - Car-T 细胞疗法数据处理与建模
=============================================

这个包提供了两个核心模块：

perfect_pipeline 模块：
----------------------
- ConstantColumnDropper: 删除常量列（如经筛选后单一疾病类型的列）
- ToxicityBinarizer: 将多分类毒性等级转换为二元分类（严重/非严重）
- DynamicFeatureAggregator: 从时间序列数据中提取聚合特征
- FullPreprocessor: 整合静态+动态特征的完整预处理器
- build_no_leak_pipeline: 构建无数据泄漏的 sklearn Pipeline

data_splitters 模块：
--------------------
- PatientLevelStratifiedSplitter: 患者级别分层数据分割（70/30）
- PatientLevelStratifiedSplitterWithCV: 带交叉验证的患者级分割
- patient_level_train_test_split: sklearn 兼容的分割函数

快速开始：
---------
```python
from pipeline import (
    ConstantColumnDropper,
    ToxicityBinarizer,
    PatientLevelStratifiedSplitter
)

# 1. 删除常量列
dropper = ConstantColumnDropper()
df_cleaned = dropper.fit_transform(df)

# 2. 二元化毒性等级
binarizer = ToxicityBinarizer(
    columns={"CRS": 2, "ICANS": 1, "Infection": 3}
)
df_final = binarizer.fit_transform(df_cleaned)

# 3. 患者级分层分割
splitter = PatientLevelStratifiedSplitter(test_size=0.3, random_state=42)
train_df, test_df = splitter.split(
    df_final,
    label_col="CRS",
    patient_id_col="ID"
)
```

详细文档请参考各模块的 docstring 和 README 文件。
"""
