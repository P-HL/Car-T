"""
静态数据转换器模块
包含各种数据类型转换的辅助函数
"""

import pandas as pd
from datetime import datetime


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
