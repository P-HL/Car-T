"""
配置管理模块
支持命令行参数、YAML配置文件、环境变量和默认值
优先顺序：命令行参数 > 配置文件 > 环境变量 > 默认值
"""

import os
import sys
import yaml
import pandas as pd
from typing import Dict, Any
import argparse


class ConfigManager:
    """
    配置管理器
    支持命令行参数、YAML配置文件、环境变量和默认值
    优先顺序：命令行参数 > 配置文件 > 环境变量 > 默认值
    """
    
    def __init__(self):
        self.config = {}
        self._load_default_config()
    
    def _load_default_config(self):
        """加载默认配置"""
        self.config = {
            # 动态数据路径配置
            'input_dir': '/home/phl/PHL/Car-T/datasetcart/processed',
            'output_dir': '/home/phl/PHL/Car-T/data_processing/output',
            
            # 静态数据处理配置
            'static_input_file': '/home/phl/PHL/Car-T/datasetcart/patient_info.csv',
            'static_output_file': '/home/phl/PHL/Car-T/data_processing/output/processed_static_data.csv',
            
            # 动态数据验证配置
            'dynamic_expected_file_count': 500,
            'dynamic_expected_row_count': 46,
            'dynamic_expected_time_range_start': -15,
            'dynamic_expected_time_range_end': 30,
            
            # 列删除配置 - 统一配置结构
            'enable_column_deletion': False,  # 默认禁用列删除
            'columns_to_delete': {
                'cbc': [2, 4, 6, 8, 10, 15, 16, 17, 18, 19, 21, 22, 23, 24],
                'biochemistry': [3, 7],
                'coagulation': [8],
                'inflammatory_biomarker': [],
                'vcn': [],
                'lymphocyte_subsets': [],
                'electrolytes': [],
                'vital_signs': [],
                'optional': []  # 可选列，如 ['VCN001', 'Lymphocyte Subsets001']
            },
            
            # 列重新排序配置
            'enable_column_reordering': True,  # 默认启用重新排序
            'column_prefixes_to_reorder': ['CBC', 'Biochemistry', 'Coagulation', 
                                           'Inflammatory Biomarker', 'Lymphocyte Subsets',
                                           'Electrolytes', 'Vital Signs'],
            
            # 可选列配置
            'optional_columns': ['VCN001'] + [f'Lymphocyte Subsets{str(i).zfill(3)}' for i in range(1, 12)],
            
            # 变量类别配置
            'variable_categories': {
                'CBC': 24,
                'Inflammatory Biomarker': 9,
                'VCN': 1,
                'Lymphocyte Subsets': 11,
                'Coagulation': 8,
                'Electrolytes': 6,
                'Biochemistry': 28,
                'Vital Signs': 6
            },
            
            # 动态数据处理配置
            'remove_optional_columns': False,
            'verbose': True,
            'progress_interval': 50,
            
            # 动态数据输出配置
            'dynamic_validation_report_path': 'dynamic_data_validation_report.txt',
            'dynamic_processing_report_path': 'dynamic_data_processing_report.txt',
            
            # 动态数据步骤控制配置
            'dynamic_validation_only': False,
            'dynamic_processing_only': False,
            'skip_interactive': False,
            
            # 静态数据特定步骤控制配置
            'static_validation_only': True,   # 静态数据默认仅验证
            'static_processing_only': False,
            
            # 静态数据验证配置
            'static_expected_column_count': 22,
            'static_expected_patient_count': 500,
            'static_validation_report_path': 'static_data_validation_report.txt',
            
            # 配置文件路径
            'config_file': None
        }
    
    def load_from_env(self):
        """从环境变量加载配置"""
        env_mapping = {
            'CART_INPUT_DIR': 'input_dir',
            'CART_OUTPUT_DIR': 'output_dir',
            'CART_STATIC_INPUT_FILE': 'static_input_file',
            'CART_STATIC_OUTPUT_FILE': 'static_output_file',
            
            # 动态数据配置
            'CART_DYNAMIC_EXPECTED_FILE_COUNT': 'dynamic_expected_file_count',
            'CART_DYNAMIC_EXPECTED_ROW_COUNT': 'dynamic_expected_row_count',
            'CART_DYNAMIC_VALIDATION_ONLY': 'dynamic_validation_only',
            'CART_DYNAMIC_PROCESSING_ONLY': 'dynamic_processing_only',
            'CART_DYNAMIC_VALIDATION_REPORT': 'dynamic_validation_report_path',
            'CART_DYNAMIC_PROCESSING_REPORT': 'dynamic_processing_report_path',
            
            'CART_ENABLE_COLUMN_DELETION': 'enable_column_deletion',
            'CART_REMOVE_OPTIONAL': 'remove_optional_columns',
            'CART_VERBOSE': 'verbose',
            'CART_PROGRESS_INTERVAL': 'progress_interval',
            'CART_SKIP_INTERACTIVE': 'skip_interactive',
            
            # 静态数据特定环境变量
            'CART_STATIC_VALIDATION_ONLY': 'static_validation_only',
            'CART_STATIC_PROCESSING_ONLY': 'static_processing_only',
            'CART_STATIC_EXPECTED_COLUMN_COUNT': 'static_expected_column_count',
            'CART_STATIC_EXPECTED_PATIENT_COUNT': 'static_expected_patient_count'
        }
        
        for env_var, config_key in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 类型转换
                if config_key in ['progress_interval', 
                                'dynamic_expected_file_count', 'dynamic_expected_row_count',
                                'static_expected_column_count', 'static_expected_patient_count']:
                    try:
                        self.config[config_key] = int(env_value)
                    except ValueError:
                        print(f"警告: 环境变量 {env_var} 的值 '{env_value}' 不是有效整数，使用默认值")
                elif config_key in ['remove_optional_columns', 'verbose', 'skip_interactive', 'enable_column_deletion',
                                  'dynamic_validation_only', 'dynamic_processing_only',
                                  'static_validation_only', 'static_processing_only']:
                    self.config[config_key] = env_value.lower() in ['true', '1', 'yes', 'on']
                else:
                    self.config[config_key] = env_value
    
    def load_from_yaml(self, config_file: str):
        """从YAML文件加载配置"""
        if not os.path.exists(config_file):
            print(f"警告: 配置文件 {config_file} 不存在，使用默认配置")
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    self.config.update(yaml_config)
                    print(f"✅ 已加载配置文件: {config_file}")
        except Exception as e:
            print(f"错误: 无法加载配置文件 {config_file}: {e}")
            sys.exit(1)
    
    def load_from_args(self, args: argparse.Namespace):
        """从命令行参数加载配置"""
        for key, value in vars(args).items():
            # argparse 对于未提供的可选参数会保留为 None
            # 但是对于 store_true/store_false 类型的布尔开关，默认值为 False
            # 我们不应让未显式提供的布尔开关(即保持为 False)覆盖来自配置文件的显式值。
            if value is None:
                continue

            # 对于布尔类型的参数，仅在用户显式设置为 True 时才覆盖配置。
            # argparse 无法区分默认的 False 和显式传入的 False，但常见用法是
            # store_true 类型的参数只在用户传入时为 True，因此只有 True 才应该覆盖配置。
            if isinstance(value, bool):
                # 如果是 False，跳过覆盖（保留配置文件/环境变量的值）
                # 这避免了默认的 False 覆盖掉配置文件里设置为 True 的情况。
                if value is False:
                    continue

            # 写入配置
            self.config[key] = value
    
    def validate_config(self):
        """验证配置的有效性"""
        # 验证路径
        required_paths = ['input_dir']
        for path_key in required_paths:
            path = self.config[path_key]
            if not os.path.exists(path):
                print(f"错误: 路径不存在: {path}")
                sys.exit(1)
        
        # 验证数值参数
        file_count = self.config.get('dynamic_expected_file_count', 0)
        row_count = self.config.get('dynamic_expected_row_count', 0)
        progress_interval = self.config.get('progress_interval', 0)
        
        if file_count <= 0:
            print("错误: dynamic_expected_file_count 必须大于0")
            sys.exit(1)
        
        if row_count <= 0:
            print("错误: dynamic_expected_row_count 必须大于0")
            sys.exit(1)
        
        if progress_interval <= 0:
            print("错误: progress_interval 必须大于0")
            sys.exit(1)
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置值"""
        self.config[key] = value
    
    def print_config(self):
        """打印当前配置"""
        print("\n当前配置:")
        print("-" * 50)
        
        # 静态数据配置部分
        print("\n🔹 静态数据配置部分:")
        static_keys = ['static_input_file', 'static_output_file', 'static_expected_column_count', 
                      'static_expected_patient_count', 'static_validation_report_path',
                      'static_validation_only', 'static_processing_only']
        for key in static_keys:
            if key in self.config:
                print(f"  {key}: {self.config[key]}")
        
        # 动态数据配置部分
        print("\n🔹 动态数据配置部分:")
        
        print("  路径配置:")
        for key in ['input_dir', 'output_dir']:
            if key in self.config:
                print(f"    {key}: {self.config[key]}")
        
        print("  验证配置:")
        dynamic_validation_keys = ['dynamic_expected_file_count', 'dynamic_expected_row_count', 
                                 'dynamic_expected_time_range_start', 'dynamic_expected_time_range_end']
        for key in dynamic_validation_keys:
            if key in self.config:
                print(f"    {key}: {self.config[key]}")
        
        print("  处理配置:")
        processing_keys = ['enable_column_deletion', 'remove_optional_columns', 'verbose', 'progress_interval']
        for key in processing_keys:
            if key in self.config:
                print(f"    {key}: {self.config[key]}")
        
        print("  步骤控制配置:")
        step_keys = ['dynamic_validation_only', 'dynamic_processing_only', 'skip_interactive']
        for key in step_keys:
            if key in self.config:
                print(f"    {key}: {self.config[key]}")
        
        print("  输出配置:")
        output_keys = ['dynamic_validation_report_path', 'dynamic_processing_report_path']
        for key in output_keys:
            if key in self.config:
                print(f"    {key}: {self.config[key]}")


def create_sample_config():
    """创建示例配置文件"""
    
    # 定义示例配置数据
    sample_data = {
        # 静态数据配置部分
        'static_input_file': '/home/phl/PHL/Car-T/datasetcart/patient_info.csv',
        'static_output_file': '/home/phl/PHL/Car-T/data_processing/output/processed_static_data.csv',
        'static_expected_column_count': 22,
        'static_expected_patient_count': 500,
        'static_validation_report_path': 'static_data_validation_report.txt',
        'static_validation_only': True,  # 静态数据默认只验证
        'static_processing_only': False,
        
        # 动态数据配置部分
        'input_dir': '/home/phl/PHL/Car-T/datasetcart/processed',
        'output_dir': '/home/phl/PHL/Car-T/datasetcart/processed_standardized',
        'dynamic_expected_file_count': 500,
        'dynamic_expected_row_count': 47,
        'dynamic_expected_time_range_start': -15,
        'dynamic_expected_time_range_end': 30,
        'enable_column_deletion': False,
        'columns_to_delete': {
            'cbc': [2, 4, 6, 8, 10, 15, 16, 17, 18, 19, 21, 22, 23, 24],
            'biochemistry': [3, 7],
            'coagulation': [8],
            'inflammatory_biomarker': [],
            'vcn': [],
            'lymphocyte_subsets': [],
            'electrolytes': [],
            'vital_signs': [],
            'optional': []  # 可选列，如 ['VCN001', 'Lymphocyte Subsets001']
        },
        'enable_column_reordering': True,
        'column_prefixes_to_reorder': ['CBC', 'Biochemistry', 'Coagulation', 
                                       'Inflammatory Biomarker', 'Lymphocyte Subsets',
                                       'Electrolytes', 'Vital Signs'],
        'remove_optional_columns': False,
        'verbose': True,
        'progress_interval': 50,
        'dynamic_validation_only': False,
        'dynamic_processing_only': False,
        'skip_interactive': False,
        'dynamic_validation_report_path': 'dynamic_data_validation_report.txt',
        'dynamic_processing_report_path': 'dynamic_data_processing_report.txt'
    }
    
    # 手动创建格式化的YAML内容，匹配目标配置文件的结构
    yaml_content = """

# CAR-T 数据处理系统配置文件

# ====================================================================================================================================
# 静态数据配置部分
# ====================================================================================================================================

# 静态数据路径配置
# ----------------------
static_input_file: {static_input_file}
static_output_file: {static_output_file}

# 静态数据验证配置
# ----------------------
static_expected_column_count: {static_expected_column_count}
static_expected_patient_count: {static_expected_patient_count}
static_validation_report_path: {static_validation_report_path}

# 静态数据步骤控制配置
# ----------------------
static_validation_only: {static_validation_only}   # 静态数据默认仅进行验证
static_processing_only: {static_processing_only}




# ====================================================================================================================================
# 动态数据配置部分
# ====================================================================================================================================

# 动态数据路径配置
# ----------------------
input_dir: {input_dir}
output_dir: {output_dir}

# 动态数据验证配置
# ----------------------
dynamic_expected_file_count: {dynamic_expected_file_count}
dynamic_expected_row_count: {dynamic_expected_row_count}
dynamic_expected_time_range_start: {dynamic_expected_time_range_start}
dynamic_expected_time_range_end: {dynamic_expected_time_range_end}

# 动态数据处理配置
# ----------------------
# 列删除配置（统一配置结构）
enable_column_deletion: {enable_column_deletion}
columns_to_delete:
  cbc:
{cbc_columns_formatted}
  biochemistry:
{biochemistry_columns_formatted}
  coagulation:
{coagulation_columns_formatted}
  inflammatory_biomarker: []  # 炎症标志物列，例如: [1, 2]
  vcn: []                     # 病毒拷贝数列，例如: [1]
  lymphocyte_subsets: []      # 淋巴细胞亚群列，例如: [1, 2, 3]
  electrolytes: []            # 电解质列，例如: [1, 2]
  vital_signs: []             # 生命体征列，例如: [1, 2, 3]
  optional: []                # 可选列（完整列名），例如: ['VCN001', 'Lymphocyte Subsets001']

# 列重新排序配置
# ----------------------
enable_column_reordering: {enable_column_reordering}
column_prefixes_to_reorder:
{reorder_prefixes_formatted}

# 动态数据处理控制配置
# ----------------------
remove_optional_columns: {remove_optional_columns}
verbose: {verbose}
progress_interval: {progress_interval}

# 动态数据步骤控制配置
# ----------------------
dynamic_validation_only: {dynamic_validation_only}
dynamic_processing_only: {dynamic_processing_only}
skip_interactive: {skip_interactive}

# 动态数据报告输出配置
# ----------------------
dynamic_validation_report_path: {dynamic_validation_report_path}
dynamic_processing_report_path: {dynamic_processing_report_path}
""".format(
        static_input_file=sample_data['static_input_file'],
        static_output_file=sample_data['static_output_file'],
        static_expected_column_count=sample_data['static_expected_column_count'],
        static_expected_patient_count=sample_data['static_expected_patient_count'],
        static_validation_report_path=sample_data['static_validation_report_path'],
        static_validation_only='true' if sample_data['static_validation_only'] else 'false',
        static_processing_only='false' if not sample_data['static_processing_only'] else 'true',
        input_dir=sample_data['input_dir'],
        output_dir=sample_data['output_dir'],
        dynamic_expected_file_count=sample_data['dynamic_expected_file_count'],
        dynamic_expected_row_count=sample_data['dynamic_expected_row_count'],
        dynamic_expected_time_range_start=sample_data['dynamic_expected_time_range_start'],
        dynamic_expected_time_range_end=sample_data['dynamic_expected_time_range_end'],
        enable_column_deletion='false' if not sample_data['enable_column_deletion'] else 'true',
        cbc_columns_formatted='\n'.join([f'    - {col}' for col in sample_data['columns_to_delete']['cbc']]),
        biochemistry_columns_formatted='\n'.join([f'    - {col}' for col in sample_data['columns_to_delete']['biochemistry']]),
        coagulation_columns_formatted='\n'.join([f'    - {col}' for col in sample_data['columns_to_delete']['coagulation']]),
        enable_column_reordering='true' if sample_data['enable_column_reordering'] else 'false',
        reorder_prefixes_formatted='\n'.join([f'  - "{prefix}"' for prefix in sample_data['column_prefixes_to_reorder']]),
        remove_optional_columns='false' if not sample_data['remove_optional_columns'] else 'true',
        verbose='true' if sample_data['verbose'] else 'false',
        progress_interval=sample_data['progress_interval'],
        dynamic_validation_only='false' if not sample_data['dynamic_validation_only'] else 'true',
        dynamic_processing_only='false' if not sample_data['dynamic_processing_only'] else 'true',
        skip_interactive='false' if not sample_data['skip_interactive'] else 'true',
        dynamic_validation_report_path=sample_data['dynamic_validation_report_path'],
        dynamic_processing_report_path=sample_data['dynamic_processing_report_path']
    )
    
    # 写入文件
    with open('config_sample.yaml', 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print("✅ 示例配置文件已创建: config_sample.yaml")
