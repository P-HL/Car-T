"""
文件总体目的：CAR-T患者静态数据的标准化处理，为机器学习模型准备数据
重要逻辑流程：数据读取→映射定义→逐列转换→结果保存的完整流程
系统依赖：与CAR-T治疗数据分析系统的关系，为后续时间序列分析做准备

===============================================================================
filepath: /home/phl/PHL/Car-T/data_encoder/data_encoder简易版/data_processed_static.py
CAR-T细胞治疗患者静态变量数据标准化编码处理模块

功能概述：
1. 读取包含CAR-T患者基础信息的CSV文件
2. 将中文编码的分类变量转换为标准化的英文编码
3. 对数值型变量进行重新分类编码
4. 统一日期格式
5. 输出标准化后的数据文件，供后续机器学习模型使用
===============================================================================
"""

import pandas as pd
import re
from datetime import datetime


def convert_csv_data(input_file, output_file):
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
    
    # 第二步：定义各类变量的标准化映射字典
    # 这些映射确保数据的一致性和可解释性
    
    # 性别编码映射 - 标准化性别表示
    sex_mapping = {
        'male': 'Male',
        'female': 'Female'
    }
    
    # 骨髓增生程度映射 - 将中文描述转换为英文标准术语
    cellularity_mapping = {
        'NA': 'NA',
        '极度减低': 'Extremely_reduced',
        '减低': 'Significantly_reduced',
        '活跃': 'Normal_active',
        '明显活跃': 'Significantly_active',
        '极度活跃': 'Extremely_active'
    }
    
    # 二元分类变量映射 - 统一"有/无"类型变量的表示
    extramedullary_mapping = {
        '无': 'No',
        '有': 'Yes'
    }  
    
    # Ann Arbor分期映射 - 淋巴瘤分期标准化
    ann_mapping = {
        'IV期': 'stage4',
        'III期': 'stage3',
        'II期': 'stage2',
        'I期': 'stage1',
        'NA': 'NA',
    }
    
    # 既往造血干细胞移植类型映射
    prior_mapping = {
        '无': 'None',
        '自体': 'Autologous',
        '异体': 'Allogeneic'
    }
    
    # 是否类型变量映射 - 标准化布尔值表示
    boolean_mapping = {
        '否': 'No',
        '是': 'Yes'
    }
    
    # CAR-T细胞共刺激分子类型映射 - 标准化CAR-T构建信息
    costimulatory_mapping = {
        '41BB': '41BB',
        'CD28': 'CD28',
        '41BB+CD28': '41BB+CD28'
    }

    # CAR-T细胞构建类型映射 - 区分单靶点、双靶点等不同构建策略
    construct_mapping = {
        'CD19+CD20 tandem': 'Tandem',
        'CD7 single target': 'Single',
        'single target cocktail': 'Cocktail',
        'CD20/22': 'Tandem',
        'CD19+CD22': 'Tandem'
    }

    # 第三步：创建数据副本进行转换，避免修改原始数据
    df_converted = df.copy()
    
    # 第四步：逐列进行数据转换
    # 每个转换都包含列存在性检查，确保代码的健壮性
    
    # 转换患者基础信息
    # 转换年龄 - 通常已为数值型，无需特殊处理
    # 转换性别 - 使用预定义映射
    if 'Sex' in df_converted.columns:
        df_converted['Sex'] = df_converted['Sex'].map(sex_mapping)
        
    # 转换疾病类型 - 使用自定义函数进行智能分类
    # 主要区分ALL类型和B细胞淋巴瘤类型
    if 'Disease' in df_converted.columns:
        df_converted['Disease'] = df_converted['Disease'].apply(convert_disease) 
    
    # 转换骨髓相关指标
    # 转换骨髓肿瘤细胞比例 - 通常已为数值型百分比
    # 转换骨髓增生程度 - 使用中文到英文的标准化映射
    if 'Bone marrow cellularity' in df_converted.columns:
        df_converted['Bone marrow cellularity'] = df_converted['Bone marrow cellularity'].map(cellularity_mapping)
    
    # 转换病变部位相关信息
    # 转换髓外大包块 - 二元分类变量
    if 'extramedullary mass' in df_converted.columns:
        df_converted['extramedullary mass'] = df_converted['extramedullary mass'].map(extramedullary_mapping)
        
    # 转换结外有无病变 - 使用自定义函数进行数值重新分类
    # 将连续数值转换为有意义的分类变量
    if 'extranodal involvement' in df_converted.columns:
        df_converted['extranodal involvement'] = df_converted['extranodal involvement'].apply(convert_extranodal)
    
    # 转换疾病分期相关信息
    # 转换B分期 - 淋巴瘤特有的全身症状指标
    if 'B symptoms' in df_converted.columns:
        df_converted['B symptoms'] = df_converted['B symptoms'].map(extramedullary_mapping)
        
    # 转换Ann Arbor分期 - 淋巴瘤标准分期系统
    if 'Ann Arbor stage' in df_converted.columns:
        df_converted['Ann Arbor stage'] = df_converted['Ann Arbor stage'].map(ann_mapping)
    
    # 转换治疗历史相关信息
    # 转换治疗线数 - 使用自定义函数进行分层
    # 治疗线数是预后的重要指标
    if 'Number of prior therapy lines' in df_converted.columns:
        df_converted['Number of prior therapy lines'] = df_converted['Number of prior therapy lines'].apply(convert_therapy_line)

    # 转换既往有无HSCT，既往有无造血干细胞移植历史
    if 'Prior hematopoietic stem cell transplantation' in df_converted.columns:
        df_converted['Prior hematopoietic stem cell transplantation'] = df_converted['Prior hematopoietic stem cell transplantation'].map(prior_mapping)

    # 转换CAR-T治疗相关信息
    # 转换桥接治疗 - CAR-T制备期间的临时治疗
    if 'Bridging therapy' in df_converted.columns:
        df_converted['Bridging therapy'] = df_converted['Bridging therapy'].map(extramedullary_mapping)
    
    # 转换自体移植序贯治疗信息
    if 'CAR-T therapy following auto-HSCT ' in df_converted.columns:
        df_converted['CAR-T therapy following auto-HSCT '] = df_converted['CAR-T therapy following auto-HSCT '].map(boolean_mapping)
    
    # 转换CAR-T细胞产品特征
    # 转换CAR-T共刺激分子类型 - 影响CAR-T细胞功能的关键因素
    if 'Costimulatory molecule' in df_converted.columns:
        df_converted['Costimulatory molecule'] = df_converted['Costimulatory molecule'].map(costimulatory_mapping)
    
    # 转换CAR-T结构类型 - 单靶点vs多靶点策略
    if 'Type of construct(tandem/single target)' in df_converted.columns:
        df_converted['Type of construct(tandem/single target)'] = df_converted['Type of construct(tandem/single target)'].map(construct_mapping)

    # 转换关键时间节点
    # 转换CAR-T回输日期 - 统一日期格式，便于时间序列分析
    if 'CAR-T cell infusion date' in df_converted.columns:
        df_converted['CAR-T cell infusion date'] = df_converted['CAR-T cell infusion date'].apply(convert_date_format)
    
    # 第五步：保存转换结果并返回
    df_converted.to_csv(output_file, index=False)
    print(f"数据转换完成，已保存到: {output_file}")
    
    return df_converted


def convert_date_format(date_str):
    """
    日期格式标准化函数
    
    功能：将多种日期格式统一转换为ISO标准格式 (YYYY-MM-DD)
    
    参数:
        date_str: 输入的日期字符串，支持格式如 "2024/5/20"
    
    返回:
        标准化后的日期字符串 "2024-05-20" 或原值（如果转换失败）
    
    处理逻辑:
        1. 检查空值和缺失值
        2. 识别斜杠分隔的日期格式
        3. 转换为标准ISO格式
        4. 异常处理确保程序稳定性
    """
    if pd.isna(date_str) or date_str == '':
        return date_str
    
    try:
        # 处理常见的 "年/月/日" 格式
        if '/' in str(date_str):
            date_obj = datetime.strptime(str(date_str), '%Y/%m/%d')
            return date_obj.strftime('%Y-%m-%d')  # 转换为ISO标准格式
        else:
            return date_str  # 如果已经是标准格式或其他格式，保持不变
    except:
        return date_str  # 转换失败时返回原值，避免数据丢失

def convert_disease(disease):
    """
    疾病类型智能分类函数
    
    功能：根据疾病名称进行二分类，区分急性淋巴细胞白血病(ALL)和B细胞非霍奇金淋巴瘤(B-NHL)
    
    参数:
        disease: 疾病名称字符串，如 "B-ALL", "DLBCL", "FL转DLBCL" 等
    
    返回:
        "ALL" - 如果疾病名称包含"ALL"
        "B-NHL" - 所有其他B细胞恶性肿瘤类型
    
    分类逻辑:
        - ALL类型：包括B-ALL、T-ALL等所有急性淋巴细胞白血病
        - B-NHL类型：包括DLBCL、MCL、FL等所有B细胞淋巴瘤
        这种分类有助于区分两大类对CAR-T治疗响应不同的疾病
    """
    if pd.isna(disease):
        return disease
    disease_str = str(disease)
    # 任何包含"ALL"的疾病类型都归类为急性淋巴细胞白血病
    if 'ALL' in disease_str:
        return 'ALL'
    # 所有其他疾病类型都归类为B细胞非霍奇金淋巴瘤
    else:
        return 'B-NHL'

def convert_extranodal(value):
    """
    结外病变累及数量分层函数
    
    功能：将结外病变累及的器官/部位数量进行有意义的分层
    
    参数:
        value: 结外病变累及数量（0-6的整数）
    
    返回:
        0 - 无结外病变
        1 - 单一结外病变  
        2 - 多发结外病变（≥2个部位）
    
    临床意义:
        - 结外病变数量是淋巴瘤预后的重要指标
        - 0个：预后最好
        - 1个：中等预后
        - ≥2个：预后较差，需要更积极的治疗
    """
    if pd.isna(value):
        return value
    try:
        val = int(value)
        if val == 0:
            return 0  # 无结外病变
        elif val == 1:
            return 1  # 单一结外病变
        elif val >= 2:
            return 2  # 多发结外病变
        else:
            return value
    except (ValueError, TypeError):
        return value  # 处理非数值输入

def convert_therapy_line(value):
    """
    既往治疗线数分层函数
    
    功能：将连续的治疗线数转换为有临床意义的分层变量
    
    参数:
        value: 既往治疗线数（1-11的整数）
    
    返回:
        1 - 一线治疗失败
        2 - 二线治疗失败
        3 - 三线治疗失败
        4 - 多线治疗失败（>3线）
    
    临床意义:
        - 治疗线数反映疾病的难治程度
        - 线数越多，预后越差，CAR-T治疗的挑战性越大
        - >3线通常被认为是重度预治疗患者
    """
    if pd.isna(value):
        return value
    try:
        val = int(value)
        if val == 1:
            return 1  # 一线治疗失败
        elif val == 2:
            return 2  # 二线治疗失败
        elif val == 3:
            return 3  # 三线治疗失败
        elif val > 3:
            return 4  # 重度预治疗（多线治疗失败）
        else:
            return value
    except (ValueError, TypeError):
        return value  # 处理非数值输入


# 主程序执行部分
if __name__ == "__main__":
    """
    脚本主入口点
    
    功能：
        1. 定义输入和输出文件路径
        2. 执行数据转换流程
        3. 显示转换结果预览
    
    文件路径说明：
        - 输入文件：包含原始CAR-T患者数据的CSV文件
        - 输出文件：标准化编码后的数据文件，可直接用于机器学习模型
    """
    # 定义文件路径 - 根据实际项目结构调整
    input_file = "/home/phl/PHL/pytorch-forecasting/datasetcart/encoded.csv"
    output_file = "/home/phl/PHL/pytorch-forecasting/datasetcart/encoded_standardized.csv"
    
    # 执行数据标准化转换
    converted_data = convert_csv_data(input_file, output_file)
    
    # 显示转换结果预览，便于验证转换效果
    print("\n转换后的数据预览:")
    print(converted_data.head())