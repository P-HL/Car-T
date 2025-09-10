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

def create_availability_heatmap(data_frames, output_path="/home/phl/PHL/Car-T/heatmap_generator/output_gemini/data_availability_heatmap.png"):
    """
    创建并保存数据可用性热图。
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
    availability_matrix = pd.DataFrame(0, index=time_points, columns=variable_groups.keys())

    # 遍历每个患者的数据
    for df in data_frames:
        # 遍历每个时间点
        for day in time_points:
            if day in df.index:
                # 遍历每个变量组
                for group_name, variables in variable_groups.items():
                    # 检查该时间点和该组中是否有任何可用数据
                    # 如果该组中的任何变量在指定日期有数据，则认为该组有数据
                    available_in_group = False
                    for var in variables:
                        if var in df.columns and pd.notna(df.loc[day, var]):
                            available_in_group = True
                            break
                    if available_in_group:
                        availability_matrix.loc[day, group_name] += 1

    # 将计数转换为可用性比例（0或1），表示至少一个患者在该时间点和变量组有数据
    # 如果该时间点和变量组有任何患者数据，则为1（黄色），否则为0（黑色）
    heatmap_data = (availability_matrix > 0).astype(int).T # 转置以便X轴为时间，Y轴为变量组

    # 绘制热图
    plt.figure(figsize=(6.3, 10))   # 调整图像大小以适应更多变量组
    sns.heatmap(
        heatmap_data,
        cmap=['black', 'yellow'],  # 0为黑色（缺失），1为黄色（可用）
        cbar=False,               # 不显示颜色条
        linewidths=0.5,           # 网格线宽度
        linecolor='gray'          # 网格线颜色
    )

    # 设置X轴刻度
    x_tick_labels = [str(day) if day % 5 == 0 else '' for day in time_points]
    plt.xticks(np.arange(len(time_points)) + 0.5, x_tick_labels, rotation=45, ha='right')
    plt.xlabel('Days (from -15 to 30)')
    plt.yticks(rotation=0)
    plt.ylabel('Variable Categories')
    plt.title('Data Availability Heatmap Across 500 Patients')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
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
        print("All patient data loaded. Generating heatmap...")
        # 创建并显示热图
        create_availability_heatmap(all_patient_data)
        print("Heatmap generated and saved as 'data_availability_heatmap.png'.")