import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def process_patient_data(file_path):
    """
    读取单个患者的CSV文件并返回一个DataFrame，其中包含处理后的数据。
    """
    df = pd.read_csv(file_path, index_col=0)
    # 将'天'列作为索引
    df.index.name = 'day'
    return df

def analyze_and_visualize_availability(data_frames, num_patients, output_csv_path="/home/phl/PHL/Car-T/heatmap_generator/output_gemini2/data_availability_fraction.csv", output_heatmap_path="/home/phl/PHL/Car-T/heatmap_generator/output_gemini2/data_availability_heatmap_percentage.png"):
    """
    分析数据可用性，导出CSV文件，并创建连续百分比热图。
    """
    # 定义变量分组
    variable_groups = {
        'CBC': [f'CBC{i:03d}' for i in range(1, 25)],
        'Inflammatory Biomarker': [f'Inflammatory Biomarker{i:03d}' for i in range(1, 10)],
        'VCN': ['VCN001'],
        'Lymphocyte Subsets': [f'Lymphocyte Subsets{i:03d}' for i in range(1, 12)],
        'Coagulation': [f'Coagulation{i:03d}' for i in range(1, 9)],
        'Electrolytes': [f'Electrolytes{i:03d}' for i in range(1, 7)],
        'Biochemistry': [f'Biochemistry{i:03d}' for i in range(1, 29)],
        'Vital Signs': [f'Vital Signs{i:03d}' for i in range(1, 7)]
    }

    # 初始化一个DataFrame来存储每个变量组和每个时间点的数据可用性计数
    # 行是时间点，列是变量组
    time_points = range(-15, 31)
    availability_counts_matrix = pd.DataFrame(0, index=time_points, columns=variable_groups.keys())

    # 遍历每个患者的数据
    for df in data_frames:
        # 遍历每个时间点
        for day in time_points:
            if day in df.index:
                # 遍历每个变量组
                for group_name, variables in variable_groups.items():
                    # 检查该时间点和该组中是否有任何可用数据
                    # 如果该组中的任何变量在指定日期有数据，则认为该组在该日期有数据
                    available_in_group = False
                    for var in variables:
                        if var in df.columns and pd.notna(df.loc[day, var]):
                            available_in_group = True
                            break
                    if available_in_group:
                        availability_counts_matrix.loc[day, group_name] += 1

    # 计算可用性覆盖率（分数从 0 到 1）
    # availability_counts_matrix 记录了在该时间点和变量组拥有数据的患者数量
    # num_patients 是总患者数
    data_availability_fraction = (availability_counts_matrix / num_patients).T # 转置以便行是类别，列是日期

    # 1. 导出 CSV 文件
    data_availability_fraction.to_csv(output_csv_path)
    print(f"Data availability fraction exported to '{output_csv_path}'")

    # 2. 更新热图可视化为连续百分比色标
    plt.figure(figsize=(9, 10))
    sns.heatmap(
        data_availability_fraction * 100, # 将分数转换为百分比
        cmap='viridis',                  # 使用连续色标，例如 'viridis', 'plasma', 'magma', 'cividis'
        cbar=True,                       # 显示颜色条
        linewidths=0.5,                  # 网格线宽度
        linecolor='gray',                # 网格线颜色
        fmt=".0f",                       # 格式化注释，显示整数百分比
        annot=False,                     # 不在每个单元格显示数值，颜色条已足够
        vmin=0, vmax=100                 # 确保色标范围从0到100
    )

    # 设置颜色条标签
    cbar = plt.gca().collections[0].colorbar
    cbar.set_label('Data Availability (%)', rotation=270, labelpad=20)

    # 设置X轴刻度
    x_tick_labels = [str(day) if day % 5 == 0 else '' for day in time_points]
    plt.xticks(np.arange(len(time_points)) + 0.5, x_tick_labels, rotation=45, ha='right')
    plt.xlabel('Days (from -15 to 30)')
    plt.yticks(rotation=0)
    plt.ylabel('Variable Categories')
    plt.title('Data Availability Heatmap Across Patients (Percentage)')
    plt.tight_layout()
    plt.savefig(output_heatmap_path, dpi=300)
    plt.show()

if __name__ == "__main__":
    processed_folder = "/home/phl/PHL/pytorch-forecasting/datasetcart/processed"
    num_patients = 2
    all_patient_data = []

    # 确保'processed'文件夹存在
    if not os.path.exists(processed_folder):
        print(f"Error: The folder '{processed_folder}' does not exist.")
        print("Please create the folder and place the patient CSV files inside.")
        exit()

    # 读取所有患者的数据
    print(f"Reading data for {num_patients} patients from '{processed_folder}'...")
    for i in range(1, num_patients + 1):
        file_name = f"{i}.csv"
        file_path = os.path.join(processed_folder, file_name)
        if os.path.exists(file_path):
            df = process_patient_data(file_path)
            all_patient_data.append(df)
        else:
            print(f"Warning: File '{file_path}' not found. Skipping patient {i}.")

    if not all_patient_data:
        print("No patient data found. Exiting.")
    else:
        print("All patient data loaded. Analyzing availability and generating output...")
        # 分析可用性、导出CSV并创建热图
        analyze_and_visualize_availability(all_patient_data, num_patients)
        print("Analysis complete. Check 'data_availability_fraction.csv' and 'data_availability_heatmap_percentage.png'.")