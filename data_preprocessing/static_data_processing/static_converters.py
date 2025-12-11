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
        date_str: 输入的日期字符串，支持格式如 "2024/5/20" 或 "YYYY/MM/DD 0:00:00"
    
    返回:
        标准化后的日期字符串 "YYYY-MM-DD" 格式，或原值（如果转换失败）
    
    处理逻辑:
        1. 检查空值和缺失值
        2. 识别斜杠分隔的日期格式（包括带时间戳的格式）
        3. 转换为标准ISO格式 YYYY-MM-DD
        4. 异常处理确保程序稳定性
    """
    if pd.isna(date_str) or date_str == '':
        return date_str
    
    try:
        # 方法改进：使用 pandas 强大的 to_datetime 自动识别格式
        # 它可以同时处理 "2025/1/15", "2025-1-15", "2025/1/15 00:00:00" 以及 datetime对象
        dt = pd.to_datetime(date_str)
        
        # 转换成功后，统一格式化为 YYYY-MM-DD
        return dt.strftime('%Y-%m-%d')
    except:
        # 如果转换失败（例如完全不是日期），返回原值的字符串形式
        return str(date_str)


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


def convert_grade_to_integer(value):
    """
    等级评分浮点数转整数函数
    
    功能：将浮点数等级值转换为整数值，用于CRS grade、ICANS grade等指标
    
    参数:
        value: 等级值，可能为浮点数（如"0.0", "1.0"）或"NA"
    
    返回:
        整数值（如"0", "1"）或"NA"
    
    处理逻辑:
        - 将浮点数值转换为对应的整数字符串
        - 保留"NA"值和NaN值不变
        - 异常处理确保程序稳定性
    """
    if pd.isna(value) or value == 'NA' or value == '':
        return value
    
    try:
        # 转换为浮点数然后转为整数
        float_val = float(value)
        # 检查是否为 NaN
        if pd.isna(float_val):
            return value
        int_val = int(float_val)
        return str(int_val)
    except (ValueError, TypeError):
        return value  # 转换失败时返回原值
