"""
静态数据处理器模块
CAR-T患者静态变量数据标准化编码处理的主要处理器
"""

import pandas as pd
from typing import Optional

from .static_converters import (
    convert_disease, 
    convert_extranodal, 
    convert_therapy_line, 
    convert_date_format
)


class StaticDataProcessor:
    """
    静态数据处理器
    用于CAR-T患者基础信息的CSV文件数据标准化转换
    """
    
    def __init__(self):
        """初始化静态数据处理器"""
        self._setup_mappings()
    
    def _setup_mappings(self):
        """设置各类变量的标准化映射字典"""
        
        # 性别编码映射 - 标准化性别表示
        self.sex_mapping = {
            'male': 'Male',
            'female': 'Female'
        }
        
        # 骨髓增生程度映射 - 将中文描述转换为英文标准术语
        self.cellularity_mapping = {
            'NA': 'NA',
            '极度减低': 'Extremely_reduced',
            '减低': 'Significantly_reduced',
            '活跃': 'Normal_active',
            '明显活跃': 'Significantly_active',
            '极度活跃': 'Extremely_active'
        }
        
        # 二元分类变量映射 - 统一"有/无"类型变量的表示
        self.extramedullary_mapping = {
            '无': 'No',
            '有': 'Yes'
        }
        
        # Ann Arbor分期映射 - 淋巴瘤分期标准化
        self.ann_mapping = {
            'IV期': 'stage4',
            'III期': 'stage3',
            'II期': 'stage2',
            'I期': 'stage1',
            'NA': 'NA',
        }
        
        # 既往造血干细胞移植类型映射
        self.prior_mapping = {
            '无': 'None',
            '自体': 'Autologous',
            '异体': 'Allogeneic'
        }
        
        # 是否类型变量映射 - 标准化布尔值表示
        self.boolean_mapping = {
            '否': 'No',
            '是': 'Yes'
        }
        
        # CAR-T细胞共刺激分子类型映射 - 标准化CAR-T构建信息
        self.costimulatory_mapping = {
            '41BB': '41BB',
            'CD28': 'CD28',
            '41BB+CD28': '41BB+CD28'
        }

        # CAR-T细胞构建类型映射 - 区分单靶点、双靶点等不同构建策略
        self.construct_mapping = {
            'CD19+CD20 tandem': 'Tandem',
            'CD7 single target': 'Single',
            'single target cocktail': 'Cocktail',
            'CD20/22': 'Tandem',
            'CD19+CD22': 'Tandem'
        }
    
    def convert_csv_data(self, input_file: str, output_file: str) -> pd.DataFrame:
        """
        主要数据转换函数 - 将CSV文件中的患者静态数据转换为标准化编码格式
        
        参数:
            input_file (str): 输入CSV文件路径，包含原始患者数据
            output_file (str): 输出CSV文件路径，保存标准化后的数据
        
        返回:
            df_converted (DataFrame): 转换后的数据框
            
        功能:
            - 处理CAR-T患者的基础临床特征
            - 统一编码格式，便于后续数据分析和机器学习
            - 支持多种数据类型的转换（分类、数值、日期）
        """
        
        # 第一步：读取原始CSV数据文件
        df = pd.read_csv(input_file)
        
        # 第二步：创建数据副本进行转换，避免修改原始数据
        df_converted = df.copy()
        
        # 第三步：逐列进行数据转换
        # 每个转换都包含列存在性检查，确保代码的健壮性
        
        # 转换患者基础信息
        # 转换年龄 - 通常已为数值型，无需特殊处理
        # 转换性别 - 使用预定义映射
        if 'Sex' in df_converted.columns:
            df_converted['Sex'] = df_converted['Sex'].map(self.sex_mapping)
            
        # 转换疾病类型 - 使用自定义函数进行智能分类
        # 主要区分ALL类型和B细胞淋巴瘤类型
        if 'Disease' in df_converted.columns:
            df_converted['Disease'] = df_converted['Disease'].apply(convert_disease) 
        
        # 转换骨髓相关指标
        # 转换骨髓肿瘤细胞比例 - 通常已为数值型百分比
        # 转换骨髓增生程度 - 使用中文到英文的标准化映射
        if 'Bone marrow cellularity' in df_converted.columns:
            df_converted['Bone marrow cellularity'] = df_converted['Bone marrow cellularity'].map(self.cellularity_mapping)
        
        # 转换病变部位相关信息
        # 转换髓外大包块 - 二元分类变量
        if 'extramedullary mass' in df_converted.columns:
            df_converted['extramedullary mass'] = df_converted['extramedullary mass'].map(self.extramedullary_mapping)
            
        # 转换结外有无病变 - 使用自定义函数进行数值重新分类
        # 将连续数值转换为有意义的分类变量
        if 'extranodal involvement' in df_converted.columns:
            df_converted['extranodal involvement'] = df_converted['extranodal involvement'].apply(convert_extranodal)
        
        # 转换疾病分期相关信息
        # 转换B分期 - 淋巴瘤特有的全身症状指标
        if 'B symptoms' in df_converted.columns:
            df_converted['B symptoms'] = df_converted['B symptoms'].map(self.extramedullary_mapping)
            
        # 转换Ann Arbor分期 - 淋巴瘤标准分期系统
        if 'Ann Arbor stage' in df_converted.columns:
            df_converted['Ann Arbor stage'] = df_converted['Ann Arbor stage'].map(self.ann_mapping)
        
        # 转换治疗历史相关信息
        # 转换治疗线数 - 使用自定义函数进行分层
        # 治疗线数是预后的重要指标
        if 'Number of prior therapy lines' in df_converted.columns:
            df_converted['Number of prior therapy lines'] = df_converted['Number of prior therapy lines'].apply(convert_therapy_line)

        # 转换既往有无HSCT，既往有无造血干细胞移植历史
        if 'Prior hematopoietic stem cell transplantation' in df_converted.columns:
            df_converted['Prior hematopoietic stem cell transplantation'] = df_converted['Prior hematopoietic stem cell transplantation'].map(self.prior_mapping)

        # 转换CAR-T治疗相关信息
        # 转换桥接治疗 - CAR-T制备期间的临时治疗
        if 'Bridging therapy' in df_converted.columns:
            df_converted['Bridging therapy'] = df_converted['Bridging therapy'].map(self.extramedullary_mapping)
        
        # 转换自体移植序贯治疗信息
        if 'CAR-T therapy following auto-HSCT ' in df_converted.columns:
            df_converted['CAR-T therapy following auto-HSCT '] = df_converted['CAR-T therapy following auto-HSCT '].map(self.boolean_mapping)
        
        # 转换CAR-T细胞产品特征
        # 转换CAR-T共刺激分子类型 - 影响CAR-T细胞功能的关键因素
        if 'Costimulatory molecule' in df_converted.columns:
            df_converted['Costimulatory molecule'] = df_converted['Costimulatory molecule'].map(self.costimulatory_mapping)
        
        # 转换CAR-T结构类型 - 单靶点vs多靶点策略
        if 'Type of construct(tandem/single target)' in df_converted.columns:
            df_converted['Type of construct(tandem/single target)'] = df_converted['Type of construct(tandem/single target)'].map(self.construct_mapping)

        # 转换关键时间节点
        # 转换CAR-T回输日期 - 统一日期格式，便于时间序列分析
        if 'CAR-T cell infusion date' in df_converted.columns:
            df_converted['CAR-T cell infusion date'] = df_converted['CAR-T cell infusion date'].apply(convert_date_format)
        
        # 第四步：保存转换结果并返回
        # 确保输出目录存在
        import os
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        df_converted.to_csv(output_file, index=False)
        print(f"数据转换完成，已保存到: {output_file}")
        
        return df_converted
    
    def process_data(self, input_file: str, output_file: Optional[str] = None) -> pd.DataFrame:
        """
        简化的数据处理接口
        
        参数:
            input_file: 输入文件路径
            output_file: 输出文件路径，如果为None则不保存文件
            
        返回:
            处理后的DataFrame
        """
        if output_file is None:
            # 如果没有指定输出文件，生成默认输出文件名
            output_file = input_file.replace('.csv', '_standardized.csv')
        
        return self.convert_csv_data(input_file, output_file)
