"""
动态患者数据处理器模块
用于清理、重命名和处理processed文件夹中的CSV文件
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import sys

# 添加父目录到路径以便导入utils模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config_manager import ConfigManager


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
        
        # 定义要删除的列 - 使用统一的列删除配置
        self.columns_to_delete = self._define_columns_to_delete()
        
        # 处理结果统计
        self.processing_results = {
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': [],
            'errors': [],
            'warnings': []
        }
    
    def _define_columns_to_delete(self) -> List[str]:
        """定义要删除的列名 - 统一配置"""
        columns_to_delete = []
        
        # 获取统一的列删除配置
        deletion_config = self.config.get('columns_to_delete', {})
        
        # CBC列要删除的
        cbc_to_delete = deletion_config.get('cbc', [])
        columns_to_delete.extend([f"CBC{str(i).zfill(3)}" for i in cbc_to_delete])
        
        # Biochemistry列要删除的
        biochemistry_to_delete = deletion_config.get('biochemistry', [])
        columns_to_delete.extend([f"Biochemistry{str(i).zfill(3)}" for i in biochemistry_to_delete])
        
        # Coagulation列要删除的
        coagulation_to_delete = deletion_config.get('coagulation', [])
        columns_to_delete.extend([f"Coagulation{str(i).zfill(3)}" for i in coagulation_to_delete])
        
        # 可选列（如果启用列删除）
        if self.config.get('enable_column_deletion', False):
            optional_columns = deletion_config.get('optional', [])
            columns_to_delete.extend(optional_columns)
        
        return columns_to_delete
    
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
                           output_file_path: str) -> Dict[str, Any]:
        """
        处理单个CSV文件
        
        Args:
            input_file_path: 输入文件路径
            output_file_path: 输出文件路径
            
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
            
            # 记录删除的列 - 使用统一配置中的列
            columns_to_delete = self.columns_to_delete.copy()
            
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
                         verbose: bool = True) -> Dict[str, Any]:
        """
        处理所有CSV文件
        
        Args:
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
        print(f"列删除功能: {'启用' if self.config.get('enable_column_deletion', False) else '禁用'}")
        
        # 显示将要删除的列配置
        deletion_config = self.config.get('columns_to_delete', {})
        cbc_to_delete = deletion_config.get('cbc', [])
        biochemistry_to_delete = deletion_config.get('biochemistry', [])
        coagulation_to_delete = deletion_config.get('coagulation', [])
        
        print(f"\n要删除的列配置:")
        print(f"- CBC列: {[f'CBC{str(i).zfill(3)}' for i in cbc_to_delete]}")
        print(f"- Biochemistry列: {[f'Biochemistry{str(i).zfill(3)}' for i in biochemistry_to_delete]}")
        print(f"- Coagulation列: {[f'Coagulation{str(i).zfill(3)}' for i in coagulation_to_delete]}")
        
        if self.config.get('enable_column_deletion', False):
            optional_columns = deletion_config.get('optional', [])
            print(f"- 可选列: {optional_columns}")
        
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
                output_file_path
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
            output_path = self.config.get('dynamic_processing_report_path')
            
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
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
