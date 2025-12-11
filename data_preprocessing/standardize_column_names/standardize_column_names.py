"""
列名标准化工具 - 替换列名中的空格为下划线
"""

import pandas as pd
import sys
from pathlib import Path

# 手动映射字典 - 可自定义特定列名的替换规则
CUSTOM_MAPPINGS = {
    # 包含空格的列名映射
    # "BM disease burden": "BM_disease_burden",
    # "Bone marrow cellularity": "Bone_marrow_cellularity",
    # "extramedullary mass": "extramedullary_mass",
    # "extranodal involvement": "extranodal_involvement",
    # "B symptoms": "B_symptoms",
    # "Ann Arbor stage": "Ann_Arbor_stage",
    # "Number of prior therapy lines": "Number_of_prior_therapy_lines",
    # "Prior hematopoietic stem cell": "Prior_hematopoietic_stem_cell",
    # "Prior CAR-T therapy": "Prior_CAR-T_therapy",
    # "Bridging therapy": "Bridging_therapy",
    # "CAR-T therapy following auto-HSCT": "CAR-T_therapy_following_auto-HSCT",
    # "Costimulatory molecule": "Costimulatory_molecule",
    # "Type of construct(tandem/single target)": "Type_of_construct(tandem/single_target)",
    # "CAR-T cell infusion date": "CAR-T_cell_infusion_date",
    # "CRS grade": "CRS_grade",
    # "ICANS grade": "ICANS_grade",
    # "Early ICAHT grade": "Early_ICAHT_grade",
    # "Late ICAHT grade": "Late_ICAHT_grade",
    # "Infection grade": "Infection_grade",
    "BM disease burden": "BMDB",
    "Bone marrow cellularity": "BMC",
    "extramedullary mass": "EM",
    "extranodal involvement": "EI",
    "B symptoms": "B_symptoms",
    "Ann Arbor stage": "AAS",
    "Number of prior therapy lines": "NL",
    "Prior hematopoietic stem cell": "PHSC",
    "Prior CAR-T therapy": "PCT",
    "Bridging therapy": "BT",
    "CAR-T therapy following auto-HSCT": "CTFA",
    "Costimulatory molecule": "CM",
    "Type of construct(tandem/single target)": "TYPE",
    "CAR-T cell infusion date": "CCID",
    "CRS grade": "CRS",
    "ICANS grade": "ICANS",
    "Early ICAHT grade": "E_ICAHT",
    "Late ICAHT grade": "L_ICAHT",
    "Infection grade": "Infection",
}


def standardize_column_names(input_file, output_file=None, custom_mappings=None):
    """
    标准化CSV文件的列名，将空格替换为下划线（保持原始数据格式）
    
    参数:
        input_file: 输入CSV文件路径
        output_file: 输出CSV文件路径（如不指定，会覆盖原文件）
        custom_mappings: 自定义列名映射字典（可选）
    
    返回:
        映射字典：{原列名: 新列名}
    """
    # 读取CSV文件 - 保持原始格式，不自动转换类型
    df = pd.read_csv(input_file, dtype=str, keep_default_na=False)
    
    # 获取原始列名
    original_columns = df.columns.tolist()
    
    # 初始化映射字典
    column_mapping = {}
    
    # 使用自定义映射
    if custom_mappings is None:
        custom_mappings = CUSTOM_MAPPINGS
    
    # 生成新列名
    for col in original_columns:
        if col in custom_mappings:
            # 使用自定义映射
            new_col = custom_mappings[col]
        else:
            # 默认规则：空格替换为下划线
            new_col = col.replace(' ', '_')
        
        column_mapping[col] = new_col
    
    # 应用列名映射
    df.rename(columns=column_mapping, inplace=True)
    
    # 确定输出文件
    if output_file is None:
        output_file = input_file
    
    # 保存文件 - 保持原始格式
    df.to_csv(output_file, index=False)
    
    # 打印映射结果
    print(f"✅ 列名标准化完成")
    print(f"📁 输入文件: {input_file}")
    print(f"📁 输出文件: {output_file}")
    print(f"\n📋 列名映射:")
    
    changed = False
    for old_col, new_col in column_mapping.items():
        if old_col != new_col:
            print(f"  '{old_col}' → '{new_col}'")
            changed = True
    
    if not changed:
        print("  (无需修改)")
    
    return column_mapping


if __name__ == "__main__":
    # 默认处理的文件路径
    default_input = "/home/phl/PHL/Car-T/data_preprocessing/output/dataset/encoded_standardized.csv"
    default_output = "/home/phl/PHL/Car-T/data_preprocessing/output/dataset/encoded_standardized_v2.csv"
    
    # 从命令行参数获取文件路径
    input_file = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_file = sys.argv[2] if len(sys.argv) > 2 else default_output
    
    # 执行标准化
    standardize_column_names(input_file, output_file)
