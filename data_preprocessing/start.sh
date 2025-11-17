#============================================================================
## 1.数据预处理脚本运行
# 动态数据：先验证，后处理
python data_processed.py --mode dynamic --validation-only --config config.yaml
python data_processed.py --mode dynamic --processing-only --config config.yaml

# 或一次性完成验证和处理
python data_processed.py --mode dynamic --validation-only --processing-only --config config.yaml

# 静态数据处理
python data_processed.py --mode static --validation-only --config config.yaml
python data_processed.py --mode static --processing-only --config config.yaml
#============================================================================
## 2.标准化列名
# 基于自定义的变量映射对数据进行重构，保留值不变，仅修改列名
python standardize_column_names/standardize_column_names.py
#============================================================================