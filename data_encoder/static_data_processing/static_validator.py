"""
静态患者数据验证器模块
用于验证encoded.csv文件的数据质量和结构一致性
"""

import os
import pandas as pd
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple
import sys

# 添加父目录到路径以便导入utils模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config_manager import ConfigManager


class StaticDataValidator:
    """
    静态患者数据验证器
    用于验证encoded.csv文件的数据质量和结构一致性
    """
    
    def __init__(self, config: ConfigManager):
        """
        初始化验证器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.static_input_file = config.get('static_input_file')
        
        # 静态数据验证配置
        self.expected_column_count = config.get('static_expected_column_count', 23)  # 更新为23列
        self.expected_patient_count = config.get('static_expected_patient_count', 700)
        
        # 定义预期的列结构和验证规则
        self.column_specs = self._define_column_specifications()
        
        # 验证结果存储
        self.validation_results = {
            'errors': [],
            'warnings': [],
            'total_patients': 0,
            'column_count': 0,
            'data_issues': []
        }
    
    def _define_column_specifications(self) -> Dict[str, Dict]:
        """定义每列的验证规范"""
        return {
            0: {  # 患者ID
                'name': '患者ID',
                'type': 'integer',
                'range': (1, 700),
                'continuous': True,
                'required': True
            },
            1: {  # 年龄
                'name': 'Age',
                'type': 'integer',
                'range': (0, 80),
                'actual_range': (0, 80),
                'required': True
            },
            2: {  # 性别
                'name': 'Sex',
                'type': 'categorical',
                'categories': ['male', 'female'],
                'required': True
            },
            3: {  # 疾病类型
                'name': 'Disease',
                'type': 'categorical',
                'skip_validation': True,  # 由于变异过多，跳过验证
                'note': '将编码为ALL/B-NHL'
            },
            4: {  # 骨髓肿瘤细胞比例
                'name': 'BM disease burden',
                'type': 'float',
                'range': (0, 100),
                'unit': '%',
                'related_to': 'leukemia'
            },
            5: {  # 骨髓增生程度
                'name': 'Bone marrow cellularity',
                'type': 'categorical',
                'categories': ['NA', '极度减低', '减低', '活跃', '明显活跃', '极度活跃'],
                'ordered': True,
                'related_to': 'leukemia'
            },
            6: {  # 髓外大包块
                'name': 'extramedullary mass',
                'type': 'categorical',
                'categories': ['有', '无'],
                'related_to': 'lymphoma'
            },
            7: {  # 结外有无病变
                'name': 'extranodal involvement',
                'type': 'categorical',
                'categories': ['0', '1', '2', '3', '4', '5', '6', '7'],
                'ordered': True,
                'note': '将编码为3类：0/1/2',
                'related_to': 'lymphoma'
            },
            8: {  # 有无B分期
                'name': 'B symptoms',
                'type': 'categorical',
                'categories': ['有', '无'],
                'related_to': 'lymphoma'
            },
            9: {  # Ann Arbor分期
                'name': 'Ann Arbor stage',
                'type': 'categorical',
                'categories': ['NA', 'I', 'II', 'III', 'IV'],
                'ordered': True,
                'related_to': 'lymphoma'
            },
            10: {  # 治疗线数
                'name': 'Number of prior therapy lines',
                'type': 'categorical',
                'categories': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'],
                'ordered': True,
                'note': '将编码为4类：1/2/3/4'
            },
            11: {  # 既往有无造血干细胞移植
                'name': 'Prior hematopoietic stem cell',
                'type': 'categorical',
                'categories': ['无', '自体', '异体']
            },
            12: {  # 既往CAR-T治疗
                'name': 'Prior CAR-T therapy',
                'type': 'categorical',
                'categories': ['有', '无'],
                'required': False,
                'note': '既往有无CAR-T治疗史，将编码为Yes/No'
            },
            13: {  # 桥接治疗
                'name': 'Bridging therapy',
                'type': 'categorical',
                'categories': ['有', '无']
            },
            14: {  # 自体移植序贯CAR-T
                'name': 'CAR-T therapy following auto-HSCT',
                'type': 'categorical',
                'categories': ['是', '否']
            },
            15: {  # CAR-T共刺激分子
                'name': 'Costimulatory molecule',
                'type': 'categorical',
                'categories': ['41BB', 'CD28', '41BB+CD28']
            },
            16: {  # CAR-T结构类型
                'name': 'Type of construct(tandem/single target)',
                'type': 'categorical',
                'skip_validation': True,  # 由于存在差异，跳过验证
                'note': '将编码为3类：Cocktail/Tandem/Single'
            },
            17: {  # CAR-T回输日期
                'name': 'CAR-T cell infusion date',
                'type': 'date',
                'format': ['YYYY/MM/DD 0:00:00'],
                'note': '将标准化为YYYY-MM-DD'
            },
            18: {  # CRS等级
                'name': 'CRS grade',
                'type': 'categorical',
                'categories': ['NA', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0'],
                'ordered': True,
                'note': '将编码为NA/0/1'
            },
            19: {  # ICANS等级
                'name': 'ICANS grade',
                'type': 'categorical',
                'categories': ['NA', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0'],
                'ordered': True,
                'note': '将编码为NA/0/1'
            },
            20: {  # 早期ICAHT等级
                'name': 'Early ICAHT grade',
                'type': 'categorical',
                'categories': ['NA', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0'],
                'ordered': True,
                'note': '将编码为NA/0/1'
            },
            21: {  # 晚期ICAHT等级
                'name': 'Late ICAHT grade',
                'type': 'categorical',
                'categories': ['NA', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0'],
                'ordered': True,
                'note': '将编码为NA/0/1'
            },
            22: {  # 感染等级
                'name': 'Infection grade',
                'type': 'categorical',
                'categories': ['NA', '0.0', '1.0', '2.0', '3.0', '4.0', '5.0'],
                'ordered': True,
                'note': '将编码为NA/0/1'
            }
        }
    
    def validate_file_structure(self, file_path: str) -> Dict[str, Any]:
        """
        验证静态数据文件的结构
        
        Args:
            file_path: 文件路径
            
        Returns:
            验证结果字典
        """
        result = {
            'file_path': file_path,
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'column_count': 0,
            'patient_count': 0,
            'data_type_issues': []
        }
        
        try:
            # 读取文件
            df = pd.read_csv(file_path)
            result['column_count'] = len(df.columns)
            result['patient_count'] = len(df)
            
            # 验证列数
            if result['column_count'] != self.expected_column_count:
                error_msg = f"列数不匹配: 预期 {self.expected_column_count} 列，实际发现 {result['column_count']} 列"
                result['errors'].append(error_msg)
                result['is_valid'] = False
            
            # 验证患者数量
            if result['patient_count'] > self.expected_patient_count:
                warning_msg = f"患者数量超出预期: 预期最多 {self.expected_patient_count} 个患者，实际发现 {result['patient_count']} 个"
                result['warnings'].append(warning_msg)
            
            # 验证各列数据
            for col_idx, col_spec in self.column_specs.items():
                if col_idx >= len(df.columns):
                    continue
                    
                col_name = df.columns[col_idx]
                col_data = df.iloc[:, col_idx]
                
                # 跳过验证的列
                if col_spec.get('skip_validation', False):
                    continue
                
                # 验证数据类型和范围
                issues = self._validate_column_data(col_data, col_spec, col_name, col_idx)
                result['data_type_issues'].extend(issues)
                
                if issues:
                    result['is_valid'] = False
            
            # 验证患者ID连续性
            if len(df.columns) > 0:
                patient_ids = df.iloc[:, 0]
                continuity_issues = self._validate_patient_id_continuity(patient_ids)
                if continuity_issues:
                    result['errors'].extend(continuity_issues)
                    result['is_valid'] = False
                    
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
    
    def _validate_column_data(self, col_data: pd.Series, col_spec: Dict, col_name: str, col_idx: int) -> List[Dict]:
        """验证单列数据"""
        issues = []
        data_type = col_spec['type']
        
        for row_idx, value in enumerate(col_data):
            # 跳过空值的验证（根据具体需求可调整）
            if pd.isna(value) or str(value).strip() == '':
                continue
            
            try:
                if data_type == 'integer':
                    # 验证整数类型和范围
                    int_val = int(float(value))
                    if 'range' in col_spec:
                        min_val, max_val = col_spec['range']
                        if not (min_val <= int_val <= max_val):
                            issues.append({
                                'type': 'range_error',
                                'column': col_name,
                                'column_index': col_idx,
                                'row': row_idx + 1,
                                'value': value,
                                'expected_range': f"{min_val}-{max_val}",
                                'message': f"值 {value} 超出预期范围 {min_val}-{max_val}"
                            })
                    
                    # 检查实际范围
                    if 'actual_range' in col_spec:
                        min_actual, max_actual = col_spec['actual_range']
                        if not (min_actual <= int_val <= max_actual):
                            issues.append({
                                'type': 'actual_range_warning',
                                'column': col_name,
                                'column_index': col_idx,
                                'row': row_idx + 1,
                                'value': value,
                                'expected_range': f"{min_actual}-{max_actual}",
                                'message': f"值 {value} 超出实际预期范围 {min_actual}-{max_actual}"
                            })
                
                elif data_type == 'float':
                    # 验证浮点数类型和范围
                    float_val = float(value)
                    if 'range' in col_spec:
                        min_val, max_val = col_spec['range']
                        if not (min_val <= float_val <= max_val):
                            issues.append({
                                'type': 'range_error',
                                'column': col_name,
                                'column_index': col_idx,
                                'row': row_idx + 1,
                                'value': value,
                                'expected_range': f"{min_val}-{max_val}",
                                'message': f"值 {value} 超出预期范围 {min_val}-{max_val}"
                            })
                
                elif data_type == 'categorical':
                    # 验证分类变量
                    str_val = str(value).strip()
                    if 'categories' in col_spec:
                        valid_categories = col_spec['categories']
                        if str_val not in valid_categories:
                            issues.append({
                                'type': 'categorical_error',
                                'column': col_name,
                                'column_index': col_idx,
                                'row': row_idx + 1,
                                'value': value,
                                'valid_categories': valid_categories,
                                'message': f"无效类别 '{value}'，有效类别: {valid_categories}"
                            })
                
                elif data_type == 'date':
                    # 验证日期格式
                    date_str = str(value).strip()
                    valid_formats = col_spec.get('format', ['YYYY-MM-DD'])
                    is_valid_date = False
                    
                    for fmt in valid_formats:
                        try:
                            if fmt == 'YYYY/MM/DD':
                                datetime.strptime(date_str, '%Y/%m/%d')
                            elif fmt == 'YYYY-MM-DD':
                                datetime.strptime(date_str, '%Y-%m-%d')
                            is_valid_date = True
                            break
                        except ValueError:
                            continue
                    
                    if not is_valid_date:
                        issues.append({
                            'type': 'date_format_error',
                            'column': col_name,
                            'column_index': col_idx,
                            'row': row_idx + 1,
                            'value': value,
                            'valid_formats': valid_formats,
                            'message': f"无效日期格式 '{value}'，有效格式: {valid_formats}"
                        })
                        
            except (ValueError, TypeError):
                issues.append({
                    'type': 'type_error',
                    'column': col_name,
                    'column_index': col_idx,
                    'row': row_idx + 1,
                    'value': value,
                    'expected_type': data_type,
                    'message': f"无法转换为 {data_type} 类型: {value}"
                })
        
        return issues
    
    def _validate_patient_id_continuity(self, patient_ids: pd.Series) -> List[str]:
        """验证患者ID的连续性"""
        issues = []
        
        try:
            # 转换为整数并排序
            id_list = [int(float(id_val)) for id_val in patient_ids if not pd.isna(id_val)]
            id_list.sort()
            
            # 检查是否从1开始
            if id_list and id_list[0] != 1:
                issues.append(f"患者ID应从1开始，实际从 {id_list[0]} 开始")
            
            # 检查连续性
            expected_id = 1
            for actual_id in id_list:
                if actual_id != expected_id:
                    issues.append(f"患者ID不连续: 期望 {expected_id}，实际 {actual_id}")
                    break
                expected_id += 1
            
            # 检查重复
            if len(set(id_list)) != len(id_list):
                duplicates = [id_val for id_val in set(id_list) if id_list.count(id_val) > 1]
                issues.append(f"发现重复的患者ID: {duplicates}")
                
        except (ValueError, TypeError) as e:
            issues.append(f"患者ID验证失败: {str(e)}")
        
        return issues
    
    def validate_static_data(self) -> Dict[str, Any]:
        """验证静态数据"""
        print("=" * 70)
        print("CAR-T治疗临床数据处理系统 - 静态数据验证")
        print("=" * 70)
        
        print(f"📂 静态数据文件: {self.static_input_file}")
        print(f"🔍 预期列数: {self.expected_column_count}")
        print(f"👥 预期最大患者数: {self.expected_patient_count}")
        print("-" * 70)
        
        # 检查文件是否存在
        if not os.path.exists(self.static_input_file):
            error_msg = f"静态数据文件不存在: {self.static_input_file}"
            self.validation_results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            return self.validation_results
        
        # 验证文件结构
        result = self.validate_file_structure(self.static_input_file)
        
        # 更新验证结果
        self.validation_results['total_patients'] = result['patient_count']
        self.validation_results['column_count'] = result['column_count']
        self.validation_results['errors'].extend(result['errors'])
        self.validation_results['warnings'].extend(result['warnings'])
        self.validation_results['data_issues'].extend(result['data_type_issues'])
        
        # 输出验证结果
        if result['is_valid']:
            print("✅ 静态数据验证通过！")
            print(f"📊 患者总数: {result['patient_count']}")
            print(f"📋 列数: {result['column_count']}")
        else:
            print("❌ 静态数据验证失败！")
            print(f"📊 患者总数: {result['patient_count']}")
            print(f"📋 列数: {result['column_count']}")
            
            if result['errors']:
                print(f"\n🚨 发现 {len(result['errors'])} 个错误:")
                for error in result['errors'][:5]:  # 只显示前5个错误
                    print(f"   • {error}")
                if len(result['errors']) > 5:
                    print(f"   ... 还有 {len(result['errors']) - 5} 个错误")
        
        if result['warnings']:
            print(f"\n⚠️  发现 {len(result['warnings'])} 个警告:")
            for warning in result['warnings'][:3]:  # 只显示前3个警告
                print(f"   • {warning}")
            if len(result['warnings']) > 3:
                print(f"   ... 还有 {len(result['warnings']) - 3} 个警告")
        
        if result['data_type_issues']:
            print(f"\n📋 发现 {len(result['data_type_issues'])} 个数据问题:")
            # 按问题类型分组显示
            issue_types = {}
            for issue in result['data_type_issues']:
                issue_type = issue['type']
                if issue_type not in issue_types:
                    issue_types[issue_type] = []
                issue_types[issue_type].append(issue)
            
            for issue_type, issues in issue_types.items():
                print(f"   📌 {issue_type}: {len(issues)} 个问题")
                for issue in issues[:2]:  # 每种类型显示前2个
                    print(f"      → 第{issue['row']}行，{issue['column']}: {issue['message']}")
                if len(issues) > 2:
                    print(f"      ... 还有 {len(issues) - 2} 个同类问题")
        
        return self.validation_results
    
    def export_validation_report(self, output_path: str = None):
        """导出详细的验证报告"""
        if output_path is None:
            output_path = self.config.get('static_validation_report_path')
            
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("静态患者数据验证报告\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"验证时间: {datetime.now()}\n")
            f.write(f"数据文件: {self.static_input_file}\n")
            f.write(f"预期列数: {self.expected_column_count}\n")
            f.write(f"预期最大患者数: {self.expected_patient_count}\n\n")
            
            f.write("验证结果汇总:\n")
            f.write(f"  实际患者数: {self.validation_results['total_patients']}\n")
            f.write(f"  实际列数: {self.validation_results['column_count']}\n")
            f.write(f"  错误数量: {len(self.validation_results['errors'])}\n")
            f.write(f"  警告数量: {len(self.validation_results['warnings'])}\n")
            f.write(f"  数据问题数量: {len(self.validation_results['data_issues'])}\n\n")
            
            if self.validation_results['errors']:
                f.write("错误详情:\n")
                for i, error in enumerate(self.validation_results['errors'], 1):
                    f.write(f"  {i}. {error}\n")
                f.write("\n")
            
            if self.validation_results['warnings']:
                f.write("警告详情:\n")
                for i, warning in enumerate(self.validation_results['warnings'], 1):
                    f.write(f"  {i}. {warning}\n")
                f.write("\n")
            
            if self.validation_results['data_issues']:
                f.write("数据问题详情:\n")
                for i, issue in enumerate(self.validation_results['data_issues'], 1):
                    f.write(f"  {i}. 列'{issue['column']}'第{issue['row']}行: {issue['message']}\n")
                f.write("\n")
            
            f.write("列规范说明:\n")
            for col_idx, col_spec in self.column_specs.items():
                f.write(f"  列{col_idx + 1} ({col_spec['name']}): {col_spec['type']}")
                if 'categories' in col_spec:
                    f.write(f", 类别: {col_spec['categories']}")
                elif 'range' in col_spec:
                    f.write(f", 范围: {col_spec['range']}")
                if col_spec.get('skip_validation'):
                    f.write(" [跳过验证]")
                if 'note' in col_spec:
                    f.write(f" - {col_spec['note']}")
                f.write("\n")
        
        print(f"✅ 验证报告已保存: {output_path}")
