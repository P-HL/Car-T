"""
动态患者数据验证器模块
用于验证processed文件夹中所有CSV文件的数据质量和结构一致性
"""

import os
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Tuple
import sys

# 添加父目录到路径以便导入utils模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config_manager import ConfigManager


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
        
        # 根据配置定义预期的列结构
        self.expected_columns = self._define_expected_columns()
        self.expected_column_count = len(self.expected_columns)
        self.expected_row_count = config.get('dynamic_expected_row_count')
        
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
            expected_time_start = self.config.get('dynamic_expected_time_range_start')
            expected_time_end = self.config.get('dynamic_expected_time_range_end')
            # 修复：包含第0天的计算，时间范围应该包括起始点、结束点和第0天
            expected_days = list(range(expected_time_start, expected_time_end + 1))
            
            # 验证配置一致性：检查dynamic_expected_row_count是否与时间范围计算一致
            calculated_row_count = expected_time_end - expected_time_start + 1  # +1 for header
            config_row_count = self.config.get('dynamic_expected_row_count')
            if calculated_row_count != config_row_count:
                warning_msg = f"配置不一致: 根据时间范围计算的行数为 {calculated_row_count}，但配置中dynamic_expected_row_count为 {config_row_count}"
                result['warnings'].append(warning_msg)
            
            # 验证实际数据行数（不含表头）是否与预期时间点数匹配
            if len(df) != len(expected_days):
                warning_msg = f"时间点数量异常: 预期 {len(expected_days)} 个时间点，实际发现 {len(df)} 个"
                result['warnings'].append(warning_msg)
                
            # 验证实际总行数（含表头）是否与配置的dynamic_expected_row_count匹配
            actual_total_rows = len(df) + 1  # +1 for header
            if actual_total_rows != config_row_count:
                warning_msg = f"总行数异常: 预期 {config_row_count} 行（含表头），实际发现 {actual_total_rows} 行"
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
                expected_time_start = self.config.get('dynamic_expected_time_range_start')
                expected_time_end = self.config.get('dynamic_expected_time_range_end')
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
        expected_file_count = self.config.get('dynamic_expected_file_count')
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
            output_path = self.config.get('dynamic_validation_report_path')
            
        # 确保输出目录存在
        import os
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
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
