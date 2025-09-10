import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- 配置路径 ---
STATIC_DATA_PATH = '/home/phl/PHL/pytorch-forecasting/datasetcart/encoded.csv'
DYNAMIC_DATA_FOLDER = '/home/phl/PHL/pytorch-forecasting/datasetcart/processed'
OUTPUT_FOLDER = './output_gemini' # 新增：用于保存图表的输出文件夹

# 确保输出文件夹存在
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# --- 1. 静态数据分析 ---

def analyze_static_data(file_path, output_folder):
    """
    分析静态数据中的缺失值并保存图表。
    """
    print("--- 正在分析静态数据 ---")
    df_static = pd.read_csv(file_path, index_col=0)

    # 计算每个变量的缺失值百分比
    missing_percentage = df_static.isnull().mean() * 100
    missing_count = df_static.isnull().sum()
    total_count = df_static.shape[0]

    # 创建一个DataFrame来存储缺失值信息
    missing_info_static = pd.DataFrame({
        'Missing Percentage': missing_percentage,
        'Missing Ratio': [f"{int(missing_count[col])}/{total_count}" for col in df_static.columns]
    })
    missing_info_static.index.name = 'Variable Category'

    # 按缺失百分比降序排序
    missing_info_static = missing_info_static.sort_values(by='Missing Percentage', ascending=False)

    print("静态数据缺失值信息:")
    print(missing_info_static)

    # 可视化静态数据缺失值
    plt.figure(figsize=(18, 8))

    # 左图：缺失数据百分比的条形图
    plt.subplot(1, 2, 1)
    sns.barplot(x=missing_info_static.index, y='Missing Percentage', data=missing_info_static, palette='viridis')
    plt.title('Static Data: Missing Value Percentage by Variable Category', fontsize=16)
    plt.xlabel('Variable Category', fontsize=12)
    plt.ylabel('Missing Percentage (%)', fontsize=12)
    plt.xticks(rotation=90, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    # 右图：数据表
    plt.subplot(1, 2, 2)
    # 创建表格并将其转换为图像
    table_data = missing_info_static.reset_index()
    table_data['Missing Percentage'] = table_data['Missing Percentage'].apply(lambda x: f"{x:.2f}%")

    ax_table = plt.gca()
    ax_table.axis('off') # 隐藏轴
    table = ax_table.table(cellText=table_data.values,
                            colLabels=table_data.columns,
                            loc='center',
                            cellLoc='center',
                            bbox=[0, 0, 1, 1]) # 调整表格大小以填充子图
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2) # 缩放表格以适应
    plt.title('Static Data: Missing Value Details', fontsize=16)
    plt.tight_layout()

    plt.suptitle('Static Data Missing Value Analysis', fontsize=20, y=1.02)
    
    # 保存静态数据分析图表
    plt.savefig(os.path.join(output_folder, 'static_data_missing_analysis.png'), bbox_inches='tight', dpi=300)
    print(f"静态数据分析图表已保存至: {os.path.join(output_folder, 'static_data_missing_analysis.png')}")
    plt.close() # 关闭图表以释放内存
    print("\n")


# --- 2. 动态数据分析 ---

def group_dynamic_variables(columns):
    """
    根据变量的前缀对动态数据变量进行分组。
    """
    grouped_variables = {}
    for col in columns:
        prefix = col[:3]
        if prefix not in grouped_variables:
            grouped_variables[prefix] = []
        grouped_variables[prefix].append(col)
    return grouped_variables

def analyze_dynamic_data(folder_path, output_folder):
    """
    分析动态数据中的缺失值并可视化，保存图表。
    """
    print("--- 正在分析动态数据 ---")

    all_patient_missing_data = []
    patient_ids = []

    # 获取所有患者的CSV文件列表
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    num_patients = len(csv_files)
    print(f"检测到 {num_patients} 位患者的动态数据。")

    # 仅从第一个CSV文件获取列名以进行分组
    if csv_files:
        first_csv_path = os.path.join(folder_path, csv_files[0])
        # 读取时跳过第一行（包含'天'），并设置第二行作为列名
        temp_df = pd.read_csv(first_csv_path, skiprows=[0])
        # 假设第一列是日期/时间，我们不分析它的缺失值，只分析其他变量
        dynamic_variables_raw = temp_df.columns[1:].tolist()
    else:
        print("未找到动态数据文件。")
        return

    # 根据前缀对动态变量进行分组
    grouped_dynamic_vars = group_dynamic_variables(dynamic_variables_raw)

    # 用于汇总每个分组类别的缺失信息
    grouped_missing_counts = {group: {'missing': 0, 'total': 0} for group in grouped_dynamic_vars.keys()}
    grouped_variable_counts = {group: len(vars) for group, vars in grouped_dynamic_vars.items()}


    # 遍历所有患者的动态数据文件
    for i, file_name in enumerate(csv_files):
        patient_id = os.path.splitext(file_name)[0]
        patient_ids.append(patient_id)
        file_path = os.path.join(folder_path, file_name)

        try:
            # 读取动态数据，跳过第一行（包含'天'），并设置第二行作为列名
            df_dynamic = pd.read_csv(file_path, skiprows=[0])
            # 同样，跳过第一列（时间）进行缺失值分析
            df_dynamic = df_dynamic.iloc[:, 1:]

            # 计算每个变量的缺失百分比
            missing_percentage = df_dynamic.isnull().mean() * 100
            
            # 存储每个患者的缺失百分比数据
            all_patient_missing_data.append(missing_percentage)

            # 更新每个分组类别的缺失计数
            for group, vars_in_group in grouped_dynamic_vars.items():
                for var in vars_in_group:
                    if var in df_dynamic.columns: # 确保变量存在
                        grouped_missing_counts[group]['total'] += 1 # 每个变量都会有45天的数据
                        grouped_missing_counts[group]['missing'] += df_dynamic[var].isnull().sum()
        except Exception as e:
            print(f"处理文件 {file_name} 时出错: {e}")
            continue
    
    # 汇总所有患者的缺失值信息
    # 计算每个分组类别的平均缺失百分比
    grouped_missing_percentage = {}
    grouped_missing_ratio = {}
    for group, counts in grouped_missing_counts.items():
        if counts['total'] > 0:
            avg_missing_percentage = (counts['missing'] / counts['total']) * 100
            grouped_missing_percentage[group] = avg_missing_percentage
            
            # 计算每个类别中缺失变量占总变量的比例
            # 这里我们统计的是至少有一个缺失值的变量
            # 重新计算每个类别中变量的缺失情况
            temp_group_missing_vars = 0
            temp_group_total_vars = 0
            for var in grouped_dynamic_vars[group]:
                # 遍历所有患者的该变量，看是否有缺失值
                has_missing_in_any_patient = False
                for patient_data in all_patient_missing_data:
                    if var in patient_data.index and patient_data[var] > 0:
                        has_missing_in_any_patient = True
                        break
                if has_missing_in_any_patient:
                    temp_group_missing_vars += 1
                temp_group_total_vars += 1 # 无论有没有缺失，都算总变量数
            
            grouped_missing_ratio[group] = f"{temp_group_missing_vars}/{temp_group_total_vars}"
        else:
            grouped_missing_percentage[group] = 0.0
            grouped_missing_ratio[group] = "0/0"

    # 将结果转换为DataFrame
    missing_info_dynamic = pd.DataFrame({
        'Missing Percentage': grouped_missing_percentage,
        'Missing Ratio': grouped_missing_ratio
    })
    missing_info_dynamic.index.name = 'Grouped Variable Category'
    missing_info_dynamic = missing_info_dynamic.sort_values(by='Missing Percentage', ascending=False)


    print("\n动态数据（按分组类别）缺失值信息:")
    print(missing_info_dynamic)

    # 可视化动态数据缺失值
    plt.figure(figsize=(18, 8))

    # 左图：缺失数据百分比的条形图
    plt.subplot(1, 2, 1)
    sns.barplot(x=missing_info_dynamic.index, y='Missing Percentage', data=missing_info_dynamic, palette='plasma')
    plt.title('Dynamic Data: Missing Value Percentage by Grouped Category (All Patients)', fontsize=16)
    plt.xlabel('Grouped Variable Category', fontsize=12)
    plt.ylabel('Average Missing Percentage (%)', fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    # 右图：数据表
    plt.subplot(1, 2, 2)
    table_data_dynamic = missing_info_dynamic.reset_index()
    table_data_dynamic['Missing Percentage'] = table_data_dynamic['Missing Percentage'].apply(lambda x: f"{x:.2f}%")

    ax_table_dynamic = plt.gca()
    ax_table_dynamic.axis('off')
    table_dynamic = ax_table_dynamic.table(cellText=table_data_dynamic.values,
                                            colLabels=table_data_dynamic.columns,
                                            loc='center',
                                            cellLoc='center',
                                            bbox=[0, 0, 1, 1])
    table_dynamic.auto_set_font_size(False)
    table_dynamic.set_fontsize(10)
    table_dynamic.scale(1.2, 1.2)
    plt.title('Dynamic Data: Missing Value Details by Grouped Category', fontsize=16)
    plt.tight_layout()

    plt.suptitle('Dynamic Data Missing Value Analysis (Grouped Categories)', fontsize=20, y=1.02)
    
    # 保存动态数据分析图表（分组类别）
    plt.savefig(os.path.join(output_folder, 'dynamic_data_grouped_missing_analysis.png'), bbox_inches='tight', dpi=300)
    print(f"动态数据（分组类别）分析图表已保存至: {os.path.join(output_folder, 'dynamic_data_grouped_missing_analysis.png')}")
    plt.close() # 关闭图表以释放内存

    # --- 所有500名患者的数据可用性模式 ---
    if all_patient_missing_data:
        print("\n--- 可视化所有患者的动态数据可用性模式 ---")
        # 将所有患者的缺失数据百分比合并为一个DataFrame
        df_all_patients_missing = pd.concat(all_patient_missing_data, axis=1)
        df_all_patients_missing.columns = patient_ids
        
        # 将数据转置，使行是患者，列是变量
        df_all_patients_missing_t = df_all_patients_missing.T

        # 创建一个二值矩阵，0表示没有缺失，1表示有缺失
        missing_pattern = (df_all_patients_missing_t > 0).astype(int)

        plt.figure(figsize=(20, 12))
        sns.heatmap(missing_pattern, cmap='viridis_r', cbar_kws={'label': 'Missing (1) / Not Missing (0)'})
        plt.title('Dynamic Data: Missing Value Pattern Across All Patients and Variables', fontsize=18)
        plt.xlabel('Dynamic Variable', fontsize=14)
        plt.ylabel('Patient ID', fontsize=14)
        plt.xticks(fontsize=8, rotation=90)
        plt.yticks(fontsize=8)
        plt.tight_layout()
        
        # 保存所有患者的数据可用性模式图表
        plt.savefig(os.path.join(output_folder, 'dynamic_data_patient_availability_heatmap.png'), bbox_inches='tight', dpi=300)
        print(f"所有患者数据可用性模式图表已保存至: {os.path.join(output_folder, 'dynamic_data_patient_availability_heatmap.png')}")
        plt.close() # 关闭图表以释放内存
    else:
        print("没有足够的动态数据来可视化所有患者的可用性模式。")


# --- 主执行部分 ---
if __name__ == "__main__":
    # 执行静态数据分析
    analyze_static_data(STATIC_DATA_PATH, OUTPUT_FOLDER)

    # 执行动态数据分析
    analyze_dynamic_data(DYNAMIC_DATA_FOLDER, OUTPUT_FOLDER)