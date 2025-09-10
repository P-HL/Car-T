import pandas as pd
import numpy as np
import os
from pathlib import Path
import warnings
from typing import Dict, List, Tuple, Optional, Any
import re
import shutil
from datetime import datetime
import argparse
import yaml
import sys


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
            # 路径配置
            'input_dir': '/home/phl/PHL/pytorch-forecasting/datasetcart/processed',
            'output_dir': '/home/phl/PHL/pytorch-forecasting/datasetcart/processed_standardized',
            'static_data_path': '/home/phl/PHL/pytorch-forecasting/datasetcart/encoded_standardized.csv',
            
            # 数据验证配置
            'expected_file_count': 500,
            'expected_row_count': 46,
            'expected_time_range_start': -15,
            'expected_time_range_end': 30,
            
            # 列删除配置
            'cbc_columns_to_delete': [2, 4, 6, 8, 10, 15, 16, 17, 18, 19, 21, 22, 23, 24],
            'biochemistry_columns_to_delete': [3, 7],
            'coagulation_columns_to_delete': [8],
            
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
            
            # 处理配置
            'remove_optional_columns': False,
            'verbose': True,
            'progress_interval': 50,
            
            # 输出配置
            'validation_report_path': 'dynamic_data_validation_report.txt',
            'processing_report_path': 'dynamic_data_processing_report.txt',
            
            # 步骤控制配置
            'enable_validation': True,
            'enable_processing': True,
            'validation_only': False,
            'processing_only': False,
            'skip_interactive': False,
            
            # 配置文件路径
            'config_file': None
        }
    
    def load_from_env(self):
        """从环境变量加载配置"""
        env_mapping = {
            'CART_INPUT_DIR': 'input_dir',
            'CART_OUTPUT_DIR': 'output_dir',
            'CART_STATIC_DATA_PATH': 'static_data_path',
            'CART_EXPECTED_FILE_COUNT': 'expected_file_count',
            'CART_EXPECTED_ROW_COUNT': 'expected_row_count',
            'CART_REMOVE_OPTIONAL': 'remove_optional_columns',
            'CART_VERBOSE': 'verbose',
            'CART_PROGRESS_INTERVAL': 'progress_interval',
            'CART_VALIDATION_REPORT': 'validation_report_path',
            'CART_PROCESSING_REPORT': 'processing_report_path',
            'CART_ENABLE_VALIDATION': 'enable_validation',
            'CART_ENABLE_PROCESSING': 'enable_processing',
            'CART_VALIDATION_ONLY': 'validation_only',
            'CART_PROCESSING_ONLY': 'processing_only',
            'CART_SKIP_INTERACTIVE': 'skip_interactive'
        }
        
        for env_var, config_key in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 类型转换
                if config_key in ['expected_file_count', 'expected_row_count', 'progress_interval']:
                    try:
                        self.config[config_key] = int(env_value)
                    except ValueError:
                        print(f"警告: 环境变量 {env_var} 的值 '{env_value}' 不是有效整数，使用默认值")
                elif config_key in ['remove_optional_columns', 'verbose', 'enable_validation', 'enable_processing', 
                                  'validation_only', 'processing_only', 'skip_interactive']:
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
            if value is not None:
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
        if self.config['expected_file_count'] <= 0:
            print("错误: expected_file_count 必须大于0")
            sys.exit(1)
        
        if self.config['expected_row_count'] <= 0:
            print("错误: expected_row_count 必须大于0")
            sys.exit(1)
        
        if self.config['progress_interval'] <= 0:
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
        for category in ['路径配置', '数据验证配置', '列删除配置', '处理配置', '步骤控制配置', '输出配置']:
            print(f"\n{category}:")
            
            if category == '路径配置':
                keys = ['input_dir', 'output_dir', 'static_data_path']
            elif category == '数据验证配置':
                keys = ['expected_file_count', 'expected_row_count', 'expected_time_range_start', 'expected_time_range_end']
            elif category == '列删除配置':
                keys = ['cbc_columns_to_delete', 'biochemistry_columns_to_delete', 'coagulation_columns_to_delete']
            elif category == '处理配置':
                keys = ['remove_optional_columns', 'verbose', 'progress_interval']
            elif category == '步骤控制配置':
                keys = ['enable_validation', 'enable_processing', 'validation_only', 'processing_only', 'skip_interactive']
            else:  # 输出配置
                keys = ['validation_report_path', 'processing_report_path']
            
            for key in keys:
                if key in self.config:
                    print(f"  {key}: {self.config[key]}")


def create_sample_config():
    """创建示例配置文件"""
    sample_config = {
        'input_dir': '/home/phl/PHL/pytorch-forecasting/datasetcart/processed',
        'output_dir': '/home/phl/PHL/pytorch-forecasting/datasetcart/processed_standardized',
        'static_data_path': '/home/phl/PHL/pytorch-forecasting/datasetcart/encoded_standardized.csv',
        'expected_file_count': 500,
        'expected_row_count': 46,
        'expected_time_range_start': -15,
        'expected_time_range_end': 30,
        'cbc_columns_to_delete': [2, 4, 6, 8, 10, 15, 16, 17, 18, 19, 21, 22, 23, 24],
        'biochemistry_columns_to_delete': [3, 7],
        'coagulation_columns_to_delete': [8],
        'remove_optional_columns': False,
        'verbose': True,
        'progress_interval': 50,
        'enable_validation': True,
        'enable_processing': True,
        'validation_only': False,
        'processing_only': False,
        'skip_interactive': False,
        'validation_report_path': 'dynamic_data_validation_report.txt',
        'processing_report_path': 'dynamic_data_processing_report.txt'
    }
    
    with open('config_sample.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(sample_config, f, default_flow_style=False, allow_unicode=True)
    
    print("✅ 示例配置文件已创建: config_sample.yaml")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='CAR-T治疗临床数据处理系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用默认配置
  python data_processed_dynamic.py
  
  # 指定输入和输出目录
  python data_processed_dynamic.py --input-dir /path/to/input --output-dir /path/to/output
  
  # 使用配置文件
  python data_processed_dynamic.py --config config.yaml
  
  # 删除可选列
  python data_processed_dynamic.py --remove-optional-columns
  
  # 只运行验证步骤
  python data_processed_dynamic.py --validation-only
  
  # 只运行处理步骤
  python data_processed_dynamic.py --processing-only
  
  # 跳过交互式询问
  python data_processed_dynamic.py --skip-interactive --remove-optional-columns
  
  # 禁用验证步骤，只运行处理
  python data_processed_dynamic.py --no-validation
  
  # 禁用处理步骤，只运行验证
  python data_processed_dynamic.py --no-processing

环境变量:
  CART_INPUT_DIR              输入目录路径
  CART_OUTPUT_DIR             输出目录路径
  CART_STATIC_DATA_PATH       静态数据文件路径
  CART_EXPECTED_FILE_COUNT    预期文件数量
  CART_EXPECTED_ROW_COUNT     预期行数
  CART_REMOVE_OPTIONAL        是否删除可选列 (true/false)
  CART_VERBOSE                是否显示详细信息 (true/false)
  CART_PROGRESS_INTERVAL      进度显示间隔
  CART_VALIDATION_REPORT      验证报告文件路径
  CART_PROCESSING_REPORT      处理报告文件路径
  CART_ENABLE_VALIDATION      是否启用验证步骤 (true/false)
  CART_ENABLE_PROCESSING      是否启用处理步骤 (true/false)
  CART_VALIDATION_ONLY        只运行验证步骤 (true/false)
  CART_PROCESSING_ONLY        只运行处理步骤 (true/false)
  CART_SKIP_INTERACTIVE       跳过交互式询问 (true/false)
        """
    )
    
    # 路径配置
    parser.add_argument('--input-dir', dest='input_dir',
                       help='输入数据目录路径')
    parser.add_argument('--output-dir', dest='output_dir',
                       help='输出数据目录路径')
    parser.add_argument('--static-data-path', dest='static_data_path',
                       help='静态数据文件路径')
    
    # 数据验证配置
    parser.add_argument('--expected-file-count', dest='expected_file_count', type=int,
                       help='预期文件数量')
    parser.add_argument('--expected-row-count', dest='expected_row_count', type=int,
                       help='预期行数')
    
    # 处理配置
    parser.add_argument('--remove-optional-columns', dest='remove_optional_columns',
                       action='store_true', help='删除可选列 (VCN001和Lymphocyte Subsets)')
    parser.add_argument('--no-verbose', dest='verbose', action='store_false',
                       help='不显示详细信息')
    parser.add_argument('--progress-interval', dest='progress_interval', type=int,
                       help='进度显示间隔')
    
    # 输出配置
    parser.add_argument('--validation-report', dest='validation_report_path',
                       help='验证报告文件路径')
    parser.add_argument('--processing-report', dest='processing_report_path',
                       help='处理报告文件路径')
    
    # 配置文件
    parser.add_argument('--config', dest='config_file',
                       help='YAML配置文件路径')
    
    # 步骤控制
    parser.add_argument('--validation-only', dest='validation_only', action='store_true',
                       help='只运行数据验证步骤')
    parser.add_argument('--processing-only', dest='processing_only', action='store_true',
                       help='只运行数据处理步骤')
    parser.add_argument('--no-validation', dest='enable_validation', action='store_false',
                       help='禁用数据验证步骤')
    parser.add_argument('--no-processing', dest='enable_processing', action='store_false',
                       help='禁用数据处理步骤')
    parser.add_argument('--skip-interactive', dest='skip_interactive', action='store_true',
                       help='跳过交互式询问，使用配置值')
    
    # 实用功能
    parser.add_argument('--create-sample-config', action='store_true',
                       help='创建示例配置文件并退出')
    parser.add_argument('--print-config', action='store_true',
                       help='打印当前配置并退出')
    
    return parser.parse_args()


class DynamicDataValidator:
    """
    动态患者数据验证器
    用于验证processed文件夹中所有CSV文件的数据质量和结构一致性
    """
    
    def __init__(self, config: ConfigManager):
        """
        初始化验证器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.processed_dir = config.get('input_dir')
        self.static_data_path = config.get('static_data_path')
        
        # 根据配置定义预期的列结构
        self.expected_columns = self._define_expected_columns()
        self.expected_column_count = len(self.expected_columns)
        self.expected_row_count = config.get('expected_row_count')
        
        # 验证结果存储
        self.validation_results = {
            'errors': [],
            'warnings': [],
            'processed_files': 0,
            'valid_files': 0,
            'invalid_files': []
        }
    
    def _define_expected_columns(self) -> List[str]:
        """定义预期的列名"""
        columns = []
        variable_categories = self.config.get('variable_categories')
        
        # 根据配置动态生成列名
        for category, count in variable_categories.items():
            if category == 'VCN':
                columns.append("VCN001")
            else:
                columns.extend([f"{category}{str(i).zfill(3)}" for i in range(1, count + 1)])
        
        return columns
    
    def _is_valid_numeric_or_na(self, value: Any) -> Tuple[bool, str]:
        """
        检查值是否为有效的数值或NA
        
        Args:
            value: 要检查的值
            
        Returns:
            (is_valid, reason): 是否有效及原因
        """
        if pd.isna(value) or value == 'NA' or value == '':
            return True, "Valid NA"
        
        try:
            float(value)
            return True, "Valid numeric"
        except (ValueError, TypeError):
            return False, f"Invalid value: {value} (type: {type(value).__name__})"
    
    def validate_file_structure(self, file_path: str) -> Dict[str, Any]:
        """
        验证单个文件的结构
        
        Args:
            file_path: 文件路径
            
        Returns:
            验证结果字典
        """
        file_name = os.path.basename(file_path)
        result = {
            'file_name': file_name,
            'file_path': file_path,
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'column_count': 0,
            'row_count': 0,
            'data_type_issues': []
        }
        
        try:
            # 读取文件
            df = pd.read_csv(file_path, index_col=0)
            result['column_count'] = len(df.columns)
            result['row_count'] = len(df) + 1  # +1 for header
            
            # 验证列数
            if result['column_count'] != self.expected_column_count:
                error_msg = f"列数不匹配: 预期 {self.expected_column_count} 列，实际发现 {result['column_count']} 列"
                result['errors'].append(error_msg)
                result['is_valid'] = False
            
            # 验证行数（时间点数）
            expected_time_start = self.config.get('expected_time_range_start')
            expected_time_end = self.config.get('expected_time_range_end')
            expected_days = list(range(expected_time_start, expected_time_end + 1))
            if len(df) != len(expected_days):
                warning_msg = f"时间点数量异常: 预期 {len(expected_days)} 个时间点，实际发现 {len(df)} 个"
                result['warnings'].append(warning_msg)
            
            # 验证列名
            actual_columns = df.columns.tolist()
            if actual_columns != self.expected_columns:
                # 检查是否只是顺序问题
                if set(actual_columns) == set(self.expected_columns):
                    result['warnings'].append("列名顺序与预期不同，但包含所有预期列")
                else:
                    missing_cols = set(self.expected_columns) - set(actual_columns)
                    extra_cols = set(actual_columns) - set(self.expected_columns)
                    
                    if missing_cols:
                        result['errors'].append(f"缺失列: {list(missing_cols)}")
                        result['is_valid'] = False
                    
                    if extra_cols:
                        result['warnings'].append(f"额外列: {list(extra_cols)}")
            
            # 验证数据类型
            for row_idx, row in df.iterrows():
                for col_idx, (col_name, value) in enumerate(row.items()):
                    is_valid, reason = self._is_valid_numeric_or_na(value)
                    if not is_valid:
                        issue = {
                            'row': row_idx,
                            'column': col_name,
                            'value': value,
                            'reason': reason,
                            'position': f"行 {row_idx}, 列 {col_name}"
                        }
                        result['data_type_issues'].append(issue)
                        result['is_valid'] = False
            
            # 检查时间索引
            try:
                time_indices = df.index.tolist()
                expected_time_start = self.config.get('expected_time_range_start')
                expected_time_end = self.config.get('expected_time_range_end')
                expected_indices = list(range(expected_time_start, expected_time_end + 1))
                if time_indices != expected_indices:
                    result['warnings'].append(f"时间索引异常: 预期 {expected_indices[:5]}...{expected_indices[-5:]}, 实际 {time_indices[:5] if len(time_indices) >= 5 else time_indices}...")
            except Exception as e:
                result['warnings'].append(f"时间索引检查失败: {str(e)}")
                
        except FileNotFoundError:
            result['errors'].append(f"文件不存在: {file_path}")
            result['is_valid'] = False
        except pd.errors.EmptyDataError:
            result['errors'].append("文件为空")
            result['is_valid'] = False
        except Exception as e:
            result['errors'].append(f"文件读取失败: {str(e)}")
            result['is_valid'] = False
        
        return result
    
    def validate_all_files(self) -> Dict[str, Any]:
        """验证所有文件"""
        print("开始验证动态患者数据文件...")
        print("=" * 60)
        
        # 获取所有CSV文件
        csv_files = list(Path(self.processed_dir).glob("*.csv"))
        total_files = len(csv_files)
        
        print(f"发现 {total_files} 个CSV文件")
        expected_file_count = self.config.get('expected_file_count')
        print(f"预期文件数量: {expected_file_count}")
        
        if total_files != expected_file_count:
            warning_msg = f"文件数量警告: 预期{expected_file_count}个文件，实际发现{total_files}个文件"
            self.validation_results['warnings'].append(warning_msg)
            print(f"⚠️  {warning_msg}")
        
        print(f"预期每个文件的列数: {self.expected_column_count}")
        print(f"预期每个文件的行数: {self.expected_row_count} (含表头)")
        print("-" * 60)
        
        # 验证每个文件
        valid_count = 0
        error_count = 0
        progress_interval = self.config.get('progress_interval')
        
        for i, file_path in enumerate(csv_files, 1):
            if i % progress_interval == 0 or i == total_files:
                print(f"进度: {i}/{total_files}")
            
            result = self.validate_file_structure(str(file_path))
            self.validation_results['processed_files'] += 1
            
            if result['is_valid']:
                valid_count += 1
            else:
                error_count += 1
                self.validation_results['invalid_files'].append(result)
                
                # 输出错误信息
                print(f"\n❌ 文件异常: {result['file_name']}")
                for error in result['errors']:
                    print(f"   错误: {error}")
                    self.validation_results['errors'].append(f"{result['file_name']}: {error}")
                
                for warning in result['warnings']:
                    print(f"   警告: {warning}")
                    self.validation_results['warnings'].append(f"{result['file_name']}: {warning}")
                
                # 输出数据类型问题
                if result['data_type_issues']:
                    print(f"   数据类型问题 ({len(result['data_type_issues'])}个):")
                    for issue in result['data_type_issues'][:5]:  # 只显示前5个
                        print(f"     - {issue['position']}: {issue['reason']}")
                    if len(result['data_type_issues']) > 5:
                        print(f"     - ... 还有 {len(result['data_type_issues']) - 5} 个类似问题")
        
        self.validation_results['valid_files'] = valid_count
        
        # 输出总结
        self._print_summary()
        
        return self.validation_results
    
    def _print_summary(self):
        """打印验证总结"""
        print("\n" + "=" * 60)
        print("验证结果总结")
        print("=" * 60)
        
        print(f"处理的文件总数: {self.validation_results['processed_files']}")
        print(f"有效文件数: {self.validation_results['valid_files']}")
        print(f"异常文件数: {len(self.validation_results['invalid_files'])}")
        print(f"错误总数: {len(self.validation_results['errors'])}")
        print(f"警告总数: {len(self.validation_results['warnings'])}")
        
        if self.validation_results['errors']:
            print(f"\n❌ 发现 {len(self.validation_results['errors'])} 个错误:")
            for error in self.validation_results['errors'][:10]:  # 显示前10个错误
                print(f"   - {error}")
            if len(self.validation_results['errors']) > 10:
                print(f"   - ... 还有 {len(self.validation_results['errors']) - 10} 个错误")
        
        if self.validation_results['warnings']:
            print(f"\n⚠️  发现 {len(self.validation_results['warnings'])} 个警告:")
            for warning in self.validation_results['warnings'][:10]:  # 显示前10个警告
                print(f"   - {warning}")
            if len(self.validation_results['warnings']) > 10:
                print(f"   - ... 还有 {len(self.validation_results['warnings']) - 10} 个警告")
        
        if len(self.validation_results['invalid_files']) == 0:
            print("\n✅ 所有文件验证通过！")
        else:
            print(f"\n❌ {len(self.validation_results['invalid_files'])} 个文件需要注意")
    
    def export_validation_report(self, output_path: str = None):
        """导出详细的验证报告"""
        if output_path is None:
            output_path = self.config.get('validation_report_path')
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("动态患者数据验证报告\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"验证时间: {pd.Timestamp.now()}\n")
            f.write(f"数据目录: {self.processed_dir}\n")
            f.write(f"预期列数: {self.expected_column_count}\n")
            f.write(f"预期行数: 46\n\n")
            
            f.write("验证结果总结:\n")
            f.write(f"- 处理文件数: {self.validation_results['processed_files']}\n")
            f.write(f"- 有效文件数: {self.validation_results['valid_files']}\n")
            f.write(f"- 异常文件数: {len(self.validation_results['invalid_files'])}\n")
            f.write(f"- 错误总数: {len(self.validation_results['errors'])}\n")
            f.write(f"- 警告总数: {len(self.validation_results['warnings'])}\n\n")
            
            if self.validation_results['errors']:
                f.write("错误列表:\n")
                f.write("-" * 40 + "\n")
                for error in self.validation_results['errors']:
                    f.write(f"❌ {error}\n")
                f.write("\n")
            
            if self.validation_results['warnings']:
                f.write("警告列表:\n")
                f.write("-" * 40 + "\n")
                for warning in self.validation_results['warnings']:
                    f.write(f"⚠️  {warning}\n")
                f.write("\n")
            
            if self.validation_results['invalid_files']:
                f.write("异常文件详情:\n")
                f.write("-" * 40 + "\n")
                for file_result in self.validation_results['invalid_files']:
                    f.write(f"\n文件: {file_result['file_name']}\n")
                    f.write(f"路径: {file_result['file_path']}\n")
                    f.write(f"列数: {file_result['column_count']} (预期: {self.expected_column_count})\n")
                    f.write(f"行数: {file_result['row_count']} (预期: 46)\n")
                    
                    if file_result['errors']:
                        f.write("错误:\n")
                        for error in file_result['errors']:
                            f.write(f"  - {error}\n")
                    
                    if file_result['warnings']:
                        f.write("警告:\n")
                        for warning in file_result['warnings']:
                            f.write(f"  - {warning}\n")
                    
                    if file_result['data_type_issues']:
                        f.write(f"数据类型问题 ({len(file_result['data_type_issues'])}个):\n")
                        for issue in file_result['data_type_issues']:
                            f.write(f"  - {issue['position']}: {issue['reason']}\n")
        
        print(f"\n📄 详细验证报告已保存至: {output_path}")


class DynamicDataProcessor:
    """
    动态患者数据处理器
    用于清理、重命名和处理processed文件夹中的CSV文件
    """
    
    def __init__(self, config: ConfigManager):
        """
        初始化处理器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.input_dir = config.get('input_dir')
        self.output_dir = config.get('output_dir')
        
        # 定义要删除的列
        self.columns_to_delete = self._define_columns_to_delete()
        
        # 定义可选删除的列（VCN001和Lymphocyte Subsets列）
        self.optional_columns = config.get('optional_columns')
        
        # 处理结果统计
        self.processing_results = {
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': [],
            'errors': [],
            'warnings': []
        }
    
    def _define_columns_to_delete(self) -> List[str]:
        """定义要删除的列名"""
        columns_to_delete = []
        
        # CBC列要删除的
        cbc_to_delete = self.config.get('cbc_columns_to_delete')
        columns_to_delete.extend([f"CBC{str(i).zfill(3)}" for i in cbc_to_delete])
        
        # Biochemistry列要删除的
        biochemistry_to_delete = self.config.get('biochemistry_columns_to_delete')
        columns_to_delete.extend([f"Biochemistry{str(i).zfill(3)}" for i in biochemistry_to_delete])
        
        # Coagulation列要删除的
        coagulation_to_delete = self.config.get('coagulation_columns_to_delete')
        columns_to_delete.extend([f"Coagulation{str(i).zfill(3)}" for i in coagulation_to_delete])
        
        return columns_to_delete
    
    def _define_optional_columns(self) -> List[str]:
        """定义可选删除的列名"""
        return self.config.get('optional_columns')
    
    def _rename_columns_with_same_prefix(self, df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        """
        重命名具有相同前缀的列，保持连续编号
        
        Args:
            df: 数据框
            prefix: 列前缀（如'CBC', 'Biochemistry', 'Coagulation'）
            
        Returns:
            重命名后的数据框
        """
        # 获取具有指定前缀的列
        prefix_columns = [col for col in df.columns if col.startswith(prefix)]
        
        if not prefix_columns:
            return df
        
        # 提取编号并排序
        column_numbers = []
        for col in prefix_columns:
            # 提取编号部分
            number_part = col.replace(prefix, "")
            try:
                number = int(number_part)
                column_numbers.append((number, col))
            except ValueError:
                # 如果不是纯数字，保持原样
                continue
        
        # 按编号排序
        column_numbers.sort(key=lambda x: x[0])
        
        # 创建重命名映射
        rename_mapping = {}
        for new_index, (old_number, old_col) in enumerate(column_numbers, 1):
            new_col = f"{prefix}{str(new_index).zfill(3)}"
            if old_col != new_col:
                rename_mapping[old_col] = new_col
        
        # 应用重命名
        if rename_mapping:
            df = df.rename(columns=rename_mapping)
        
        return df
    
    def process_single_file(self, 
                           input_file_path: str, 
                           output_file_path: str,
                           remove_optional_columns: bool = False) -> Dict[str, Any]:
        """
        处理单个CSV文件
        
        Args:
            input_file_path: 输入文件路径
            output_file_path: 输出文件路径
            remove_optional_columns: 是否删除可选列
            
        Returns:
            处理结果字典
        """
        file_name = os.path.basename(input_file_path)
        result = {
            'file_name': file_name,
            'success': False,
            'original_columns': 0,
            'final_columns': 0,
            'deleted_columns': [],
            'renamed_columns': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # 读取文件
            df = pd.read_csv(input_file_path, index_col=0)
            result['original_columns'] = len(df.columns)
            
            # 记录删除的列
            columns_to_delete = self.columns_to_delete.copy()
            if remove_optional_columns:
                columns_to_delete.extend(self.optional_columns)
            
            # 删除指定列
            deleted_columns = []
            for col in columns_to_delete:
                if col in df.columns:
                    df = df.drop(columns=[col])
                    deleted_columns.append(col)
                else:
                    result['warnings'].append(f"要删除的列 '{col}' 不存在于文件中")
            
            result['deleted_columns'] = deleted_columns
            
            # 重命名具有相同前缀的列
            prefixes_to_rename = ['CBC', 'Biochemistry', 'Coagulation']
            
            for prefix in prefixes_to_rename:
                # 记录重命名前的列名
                old_columns = [col for col in df.columns if col.startswith(prefix)]
                
                # 执行重命名
                df = self._rename_columns_with_same_prefix(df, prefix)
                
                # 记录重命名映射
                new_columns = [col for col in df.columns if col.startswith(prefix)]
                if len(old_columns) == len(new_columns):
                    for old_col, new_col in zip(sorted(old_columns), sorted(new_columns)):
                        if old_col != new_col:
                            result['renamed_columns'][old_col] = new_col
            
            result['final_columns'] = len(df.columns)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            
            # 保存处理后的文件
            df.to_csv(output_file_path)
            result['success'] = True
            
        except FileNotFoundError:
            result['errors'].append(f"文件不存在: {input_file_path}")
        except pd.errors.EmptyDataError:
            result['errors'].append("文件为空")
        except Exception as e:
            result['errors'].append(f"处理失败: {str(e)}")
        
        return result
    
    def process_all_files(self, 
                         remove_optional_columns: bool = False,
                         verbose: bool = True) -> Dict[str, Any]:
        """
        处理所有CSV文件
        
        Args:
            remove_optional_columns: 是否删除可选列（VCN001和Lymphocyte Subsets）
            verbose: 是否显示详细信息
            
        Returns:
            处理结果统计
        """
        print(f"开始处理动态患者数据文件...")
        print("=" * 70)
        
        # 获取所有CSV文件
        csv_files = list(Path(self.input_dir).glob("*.csv"))
        total_files = len(csv_files)
        
        print(f"输入目录: {self.input_dir}")
        print(f"输出目录: {self.output_dir}")
        print(f"发现 {total_files} 个CSV文件")
        print(f"可选列删除: {'是' if remove_optional_columns else '否'}")
        
        # 显示将要删除的列
        cbc_to_delete = self.config.get('cbc_columns_to_delete')
        biochemistry_to_delete = self.config.get('biochemistry_columns_to_delete')
        coagulation_to_delete = self.config.get('coagulation_columns_to_delete')
        
        print(f"\n要删除的列:")
        print(f"- CBC列: {[f'CBC{str(i).zfill(3)}' for i in cbc_to_delete]}")
        print(f"- Biochemistry列: {[f'Biochemistry{str(i).zfill(3)}' for i in biochemistry_to_delete]}")
        print(f"- Coagulation列: {[f'Coagulation{str(i).zfill(3)}' for i in coagulation_to_delete]}")
        
        if remove_optional_columns:
            print(f"- 可选列: {self.optional_columns}")
        
        print("-" * 70)
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 处理进度统计
        successful_count = 0
        failed_count = 0
        
        # 处理每个文件
        progress_interval = self.config.get('progress_interval')
        for i, input_file_path in enumerate(csv_files, 1):
            if verbose and (i % progress_interval == 0 or i == total_files):
                print(f"进度: {i}/{total_files}")
            
            # 构建输出文件路径
            file_name = input_file_path.name
            output_file_path = os.path.join(self.output_dir, file_name)
            
            # 处理文件
            result = self.process_single_file(
                str(input_file_path), 
                output_file_path, 
                remove_optional_columns
            )
            
            self.processing_results['processed_files'] += 1
            
            if result['success']:
                successful_count += 1
                if verbose and result['warnings']:
                    print(f"\n⚠️  文件 {result['file_name']} 有警告:")
                    for warning in result['warnings']:
                        print(f"   - {warning}")
            else:
                failed_count += 1
                self.processing_results['failed_files'].append(result)
                
                # 输出错误信息
                print(f"\n❌ 文件处理失败: {result['file_name']}")
                for error in result['errors']:
                    print(f"   错误: {error}")
                    self.processing_results['errors'].append(f"{result['file_name']}: {error}")
                
                for warning in result['warnings']:
                    print(f"   警告: {warning}")
                    self.processing_results['warnings'].append(f"{result['file_name']}: {warning}")
        
        self.processing_results['successful_files'] = successful_count
        
        # 输出处理总结
        self._print_processing_summary()
        
        return self.processing_results
    
    def _print_processing_summary(self):
        """打印处理总结"""
        print("\n" + "=" * 70)
        print("数据处理结果总结")
        print("=" * 70)
        
        print(f"处理的文件总数: {self.processing_results['processed_files']}")
        print(f"成功处理的文件: {self.processing_results['successful_files']}")
        print(f"处理失败的文件: {len(self.processing_results['failed_files'])}")
        print(f"错误总数: {len(self.processing_results['errors'])}")
        print(f"警告总数: {len(self.processing_results['warnings'])}")
        
        if self.processing_results['errors']:
            print(f"\n❌ 发现 {len(self.processing_results['errors'])} 个错误:")
            for error in self.processing_results['errors'][:10]:  # 显示前10个错误
                print(f"   - {error}")
            if len(self.processing_results['errors']) > 10:
                print(f"   - ... 还有 {len(self.processing_results['errors']) - 10} 个错误")
        
        if self.processing_results['warnings']:
            print(f"\n⚠️  发现 {len(self.processing_results['warnings'])} 个警告:")
            for warning in self.processing_results['warnings'][:5]:  # 显示前5个警告
                print(f"   - {warning}")
            if len(self.processing_results['warnings']) > 5:
                print(f"   - ... 还有 {len(self.processing_results['warnings']) - 5} 个警告")
        
        if len(self.processing_results['failed_files']) == 0:
            print("\n✅ 所有文件处理完成！")
            print(f"📁 处理后的文件保存在: {self.output_dir}")
        else:
            print(f"\n❌ {len(self.processing_results['failed_files'])} 个文件处理失败")
    
    def export_processing_report(self, output_path: str = None):
        """导出详细的处理报告"""
        if output_path is None:
            output_path = self.config.get('processing_report_path')
            
        cbc_to_delete = self.config.get('cbc_columns_to_delete')
        biochemistry_to_delete = self.config.get('biochemistry_columns_to_delete')
        coagulation_to_delete = self.config.get('coagulation_columns_to_delete')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("动态患者数据处理报告\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"处理时间: {datetime.now()}\n")
            f.write(f"输入目录: {self.input_dir}\n")
            f.write(f"输出目录: {self.output_dir}\n\n")
            
            f.write("删除的列:\n")
            f.write(f"- CBC列: {[f'CBC{str(i).zfill(3)}' for i in cbc_to_delete]}\n")
            f.write(f"- Biochemistry列: {[f'Biochemistry{str(i).zfill(3)}' for i in biochemistry_to_delete]}\n")
            f.write(f"- Coagulation列: {[f'Coagulation{str(i).zfill(3)}' for i in coagulation_to_delete]}\n\n")
            
            f.write("处理结果总结:\n")
            f.write(f"- 处理文件数: {self.processing_results['processed_files']}\n")
            f.write(f"- 成功文件数: {self.processing_results['successful_files']}\n")
            f.write(f"- 失败文件数: {len(self.processing_results['failed_files'])}\n")
            f.write(f"- 错误总数: {len(self.processing_results['errors'])}\n")
            f.write(f"- 警告总数: {len(self.processing_results['warnings'])}\n\n")
            
            if self.processing_results['errors']:
                f.write("错误列表:\n")
                f.write("-" * 40 + "\n")
                for error in self.processing_results['errors']:
                    f.write(f"❌ {error}\n")
                f.write("\n")
            
            if self.processing_results['warnings']:
                f.write("警告列表:\n")
                f.write("-" * 40 + "\n")
                for warning in self.processing_results['warnings']:
                    f.write(f"⚠️  {warning}\n")
                f.write("\n")
            
            if self.processing_results['failed_files']:
                f.write("失败文件详情:\n")
                f.write("-" * 40 + "\n")
                for file_result in self.processing_results['failed_files']:
                    f.write(f"\n文件: {file_result['file_name']}\n")
                    
                    if file_result['errors']:
                        f.write("错误:\n")
                        for error in file_result['errors']:
                            f.write(f"  - {error}\n")
                    
                    if file_result['warnings']:
                        f.write("警告:\n")
                        for warning in file_result['warnings']:
                            f.write(f"  - {warning}\n")
        
        print(f"\n📄 详细处理报告已保存至: {output_path}")


class StepExecutor:
    """
    步骤执行器
    管理数据验证和处理步骤的执行
    """
    
    def __init__(self, config: ConfigManager):
        """
        初始化步骤执行器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.validation_results = None
        self.processing_results = None
    
    def validate_step_configuration(self):
        """验证步骤配置的有效性"""
        validation_only = self.config.get('validation_only')
        processing_only = self.config.get('processing_only')
        enable_validation = self.config.get('enable_validation')
        enable_processing = self.config.get('enable_processing')
        
        # 检查互斥选项
        if validation_only and processing_only:
            print("错误: 不能同时指定 --validation-only 和 --processing-only")
            sys.exit(1)
        
        # 应用专用步骤设置
        if validation_only:
            self.config.set('enable_validation', True)
            self.config.set('enable_processing', False)
        elif processing_only:
            self.config.set('enable_validation', False)
            self.config.set('enable_processing', True)
        
        # 检查是否至少启用一个步骤
        final_validation = self.config.get('enable_validation')
        final_processing = self.config.get('enable_processing')
        
        if not final_validation and not final_processing:
            print("错误: 必须至少启用一个步骤（验证或处理）")
            sys.exit(1)
    
    def print_execution_plan(self):
        """打印执行计划"""
        enable_validation = self.config.get('enable_validation')
        enable_processing = self.config.get('enable_processing')
        skip_interactive = self.config.get('skip_interactive')
        
        print("\n📋 执行计划:")
        print("-" * 50)
        
        if enable_validation:
            print("✅ 数据验证步骤: 启用")
        else:
            print("❌ 数据验证步骤: 禁用")
        
        if enable_processing:
            print("✅ 数据处理步骤: 启用")
        else:
            print("❌ 数据处理步骤: 禁用")
        
        if skip_interactive:
            print("⚙️  交互模式: 禁用（使用配置值）")
        else:
            print("⚙️  交互模式: 启用")
        
        print("-" * 50)
    
    def execute_validation_step(self) -> bool:
        """
        执行数据验证步骤
        
        Returns:
            bool: 验证是否成功
        """
        if not self.config.get('enable_validation'):
            print("⏭️  跳过数据验证步骤（已禁用）")
            return True
        
        print("\n🔍 执行数据验证步骤")
        print("=" * 60)
        
        validator = DynamicDataValidator(self.config)
        print(f"预期变量类别总数: {validator.expected_column_count}")
        print("变量类别分布:")
        
        variable_categories = self.config.get('variable_categories')
        for category, count in variable_categories.items():
            if category == 'VCN':
                print(f"- {category}: {count}个变量 ({category}001)")
            else:
                print(f"- {category}: {count}个变量 ({category}001-{category}{str(count).zfill(3)})")
        
        # 执行验证
        self.validation_results = validator.validate_all_files()
        validator.export_validation_report()
        
        # 检查验证结果
        has_valid_files = self.validation_results['valid_files'] > 0
        
        if has_valid_files:
            print(f"✅ 验证完成：发现 {self.validation_results['valid_files']} 个有效文件")
        else:
            print("❌ 验证失败：没有发现有效文件")
        
        return has_valid_files
    
    def execute_processing_step(self, validation_success: bool = True) -> bool:
        """
        执行数据处理步骤
        
        Args:
            validation_success: 验证步骤是否成功
            
        Returns:
            bool: 处理是否成功
        """
        if not self.config.get('enable_processing'):
            print("⏭️  跳过数据处理步骤（已禁用）")
            return True
        
        # 如果启用了验证步骤但验证失败，则跳过处理
        enable_validation = self.config.get('enable_validation')
        if enable_validation and not validation_success:
            print("⏭️  跳过数据处理步骤（验证步骤失败）")
            return False
        
        print("\n🔧 执行数据处理步骤")
        print("=" * 60)
        
        # 确定是否删除可选列
        remove_optional = self._determine_optional_columns_removal()
        
        if remove_optional:
            print("✅ 将删除可选列")
        else:
            print("✅ 将保留可选列")
        
        # 创建处理器并执行处理
        processor = DynamicDataProcessor(self.config)
        self.processing_results = processor.process_all_files(
            remove_optional_columns=remove_optional,
            verbose=self.config.get('verbose')
        )
        
        # 导出处理报告
        processor.export_processing_report()
        
        # 检查处理结果
        success = self.processing_results['successful_files'] > 0
        
        if success:
            print(f"✅ 处理完成：成功处理 {self.processing_results['successful_files']} 个文件")
            print(f"📁 处理后的文件位于: {processor.output_dir}")
        else:
            print("❌ 处理失败：没有成功处理任何文件")
        
        return success
    
    def _determine_optional_columns_removal(self) -> bool:
        """确定是否删除可选列"""
        remove_optional = self.config.get('remove_optional_columns')
        skip_interactive = self.config.get('skip_interactive')
        
        # 如果已经通过配置指定或跳过交互，直接返回配置值
        if remove_optional or skip_interactive:
            return remove_optional
        
        # 交互式询问
        print("\n配置选项:")
        print("是否删除可选列（VCN001和Lymphocyte Subsets001-011）？")
        print("1. 是 - 删除所有可选列")
        print("2. 否 - 保留可选列（默认）")
        
        choice = input("请选择 (1/2，默认为2): ").strip()
        return choice == "1"
    
    def execute_all_steps(self):
        """执行所有启用的步骤"""
        self.validate_step_configuration()
        self.print_execution_plan()
        
        # 执行验证步骤
        validation_success = self.execute_validation_step()
        
        # 执行处理步骤
        processing_success = self.execute_processing_step(validation_success)
        
        # 打印最终结果
        self._print_final_results(validation_success, processing_success)
    
    def _print_final_results(self, validation_success: bool, processing_success: bool):
        """打印最终执行结果"""
        print("\n" + "=" * 80)
        print("执行结果总结")
        print("=" * 80)
        
        enable_validation = self.config.get('enable_validation')
        enable_processing = self.config.get('enable_processing')
        
        if enable_validation:
            if validation_success:
                print("✅ 数据验证步骤: 成功完成")
                if self.validation_results:
                    print(f"   - 处理文件数: {self.validation_results['processed_files']}")
                    print(f"   - 有效文件数: {self.validation_results['valid_files']}")
            else:
                print("❌ 数据验证步骤: 执行失败")
        
        if enable_processing:
            if processing_success:
                print("✅ 数据处理步骤: 成功完成")
                if self.processing_results:
                    print(f"   - 处理文件数: {self.processing_results['processed_files']}")
                    print(f"   - 成功文件数: {self.processing_results['successful_files']}")
            else:
                print("❌ 数据处理步骤: 执行失败")
        
        overall_success = (not enable_validation or validation_success) and (not enable_processing or processing_success)
        
        if overall_success:
            print("\n🎉 所有步骤执行完成！")
        else:
            print("\n❌ 部分步骤执行失败，请检查报告文件了解详情")
        
        print("=" * 80)


# ==================== 主执行部分 ====================

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()
    
    # 处理实用功能
    if args.create_sample_config:
        create_sample_config()
        sys.exit(0)
    
    # 初始化配置管理器
    config = ConfigManager()
    
    # 按优先顺序加载配置
    config.load_from_env()  # 环境变量
    
    if args.config_file:  # 配置文件
        config.load_from_yaml(args.config_file)
    
    config.load_from_args(args)  # 命令行参数
    
    # 打印配置信息
    if args.print_config:
        config.print_config()
        sys.exit(0)
    
    # 验证配置
    config.validate_config()
    
    print("=" * 80)
    print("CAR-T治疗临床数据处理系统")
    print("=" * 80)
    
    # 创建并执行步骤
    executor = StepExecutor(config)
    executor.execute_all_steps()