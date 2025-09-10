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

def generate_heatmap(data, title, cbar_label, cmap, vmin, vmax, ax, time_points=None):
    """
    生成单个热图的通用函数。
    """
    sns.heatmap(
        data,
        cmap=cmap,
        cbar=True,
        linewidths=0.5,
        linecolor='lightgray', # 使用更浅的网格线颜色，避免分散注意力
        fmt=".0f",
        annot=False,
        vmin=vmin,
        vmax=vmax,
        ax=ax,
        cbar_kws={"label": cbar_label, "orientation": "vertical", "pad": 0.03} # 调整颜色条标签和位置
    )
    ax.set_title(title, fontsize=36, fontweight='bold')
    ax.set_xlabel('Days (from -15 to 30)', fontsize=36)
    ax.set_ylabel('Variable Categories', fontsize=36)

    # 设置X轴刻度
    if time_points is not None:
        x_tick_labels = [str(day) if day % 5 == 0 else '' for day in time_points]
        ax.set_xticks(np.arange(len(time_points)) + 0.5)
        ax.set_xticklabels(x_tick_labels, rotation=45, ha='right', fontsize=25)
    ax.tick_params(axis='y', rotation=0, labelsize=25)

def analyze_and_visualize_data(data_frames, num_patients, config):
    """
    分析数据可用性，导出CSV文件，并根据配置生成热图。
    """
    # 确保输出文件夹存在
    if not os.path.exists(config['output_folder']):
        os.makedirs(config['output_folder'])
        print(f"Created output folder: '{config['output_folder']}'")

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

    time_points = range(-15, 31)
    availability_counts_matrix = pd.DataFrame(0, index=time_points, columns=variable_groups.keys())

    for df in data_frames:
        for day in time_points:
            if day in df.index:
                for group_name, variables in variable_groups.items():
                    available_in_group = False
                    for var in variables:
                        if var in df.columns and pd.notna(df.loc[day, var]):
                            available_in_group = True
                            break
                    if available_in_group:
                        availability_counts_matrix.loc[day, group_name] += 1

    # 计算可用性覆盖率（分数从 0 到 1）
    data_availability_fraction = (availability_counts_matrix / num_patients).T 

    # 计算缺失值百分比（0-100 整数）
    data_missing_percentage = ((1 - data_availability_fraction) * 100).astype(int)

    # 导出 CSV 文件
    if config['export_csv_availability']:
        output_availability_fraction_csv_path = os.path.join(config['output_folder'], f"data_availability_fraction.{config['csv_export_format']}")
        data_availability_fraction.to_csv(output_availability_fraction_csv_path)
        print(f"Data availability fraction exported to '{output_availability_fraction_csv_path}'")

    if config['export_csv_missing']:
        output_missing_percentage_csv_path = os.path.join(config['output_folder'], f"data_missing_percentage.{config['csv_export_format']}")
        data_missing_percentage.to_csv(output_missing_percentage_csv_path)
        print(f"Data missing percentage (0-100) exported to '{output_missing_percentage_csv_path}'")


    # 热图生成
    if config['generate_heatmap_availability'] or config['generate_heatmap_missing']:
        
        plt.style.use('seaborn-v0_8-whitegrid') # 尝试使用更专业的matplotlib样式
        
        if config['heatmap_layout'] == 'side_by_side' and config['generate_heatmap_availability'] and config['generate_heatmap_missing']:
            # 并排显示双热图
            fig, axes = plt.subplots(1, 2, figsize=config['figsize_double'], dpi=config['dpi'])
            
            # 覆盖率热图
            generate_heatmap(
                data_availability_fraction * 100,
                'Data Coverage (%)',
                'Coverage (%)',
                config['cmap_availability'],
                0, 100,
                ax=axes[0],
                time_points=time_points
            )
            
            # 缺失/缺口热图
            generate_heatmap(
                data_missing_percentage,
                'Missing Data (%)',
                'Missing (%)',
                config['cmap_missing'],
                0, 100,
                ax=axes[1],
                time_points=time_points
            )
            plt.tight_layout()
            output_file_path = os.path.join(config['output_folder'], f"heatmap_coverage_and_missing_side_by_side.{config['output_format']}")
            plt.savefig(output_file_path, format=config['output_format'])
            print(f"Side-by-side heatmaps saved to '{output_file_path}'")
            plt.show()

        else: # 单独显示或仅生成一个
            if config['generate_heatmap_availability']:
                fig, ax = plt.subplots(1, 1, figsize=config['figsize_single'], dpi=config['dpi'])
                generate_heatmap(
                    data_availability_fraction * 100,
                    'Data Coverage (%)',
                    'Coverage (%)',
                    config['cmap_availability'],
                    0, 100,
                    ax=ax,
                    time_points=time_points
                )
                plt.tight_layout()
                output_file_path = os.path.join(config['output_folder'], f"heatmap_coverage.{config['output_format']}")
                plt.savefig(output_file_path, format=config['output_format'])
                print(f"Coverage heatmap saved to '{output_file_path}'")
                plt.show()

            if config['generate_heatmap_missing']:
                fig, ax = plt.subplots(1, 1, figsize=config['figsize_single'], dpi=config['dpi'])
                generate_heatmap(
                    data_missing_percentage,
                    'Missing Data (%)',
                    'Missing (%)',
                    config['cmap_missing'],
                    0, 100,
                    ax=ax,
                    time_points=time_points
                )
                plt.tight_layout()
                output_file_path = os.path.join(config['output_folder'], f"heatmap_missing.{config['output_format']}")
                plt.savefig(output_file_path, format=config['output_format'])
                print(f"Missing data heatmap saved to '{output_file_path}'")
                plt.show()

if __name__ == "__main__":
    processed_folder = "/home/phl/PHL/pytorch-forecasting/datasetcart/processed"
    num_patients = 2
    all_patient_data = []

    # --- 配置选项 ---
    config = {
        # 输出文件夹
        'output_folder': '/home/phl/PHL/Car-T/heatmap_generator/output_gemini3', # 所有生成的CSV和图像文件将保存到此文件夹

        # CSV 导出选项
        'export_csv_availability': True,  # 导出可用性分数 (0-1) CSV
        'export_csv_missing': True,       # 导出缺失百分比 (0-100 整数) CSV
        'csv_export_format': 'csv',       # CSV 导出格式 (例如: 'csv')

        # 热图生成选项
        'generate_heatmap_availability': True, # 生成覆盖率热图
        'generate_heatmap_missing': False,      # 生成缺失/缺口热图

        # 热图布局：'separate' (单独显示) 或 'side_by_side' (并排显示，仅当 generate_heatmap_availability 和 generate_heatmap_missing 都为 True 时有效)
        'heatmap_layout': 'separate',  

        # 输出格式：'png', 'pdf', 'svg'
        'output_format': 'png',           

        # 配色方案选择
        'cmap_availability': 'viridis',    # 覆盖率热图的颜色映射 (0% 覆盖 -> 紫色, 100% 覆盖 -> 黄色)
        'cmap_missing': 'Blues',           # 缺失热图的颜色映射 (0% 缺失 -> 白色, 100% 缺失 -> 深蓝色)
                                           # 其他选择如 'RdYlGn_r' (红色-黄色-绿色 反转), 'YlOrRd' (黄-橙-红)

        # 图形大小和分辨率
        'figsize_single': (42, 24),         # 单个热图的图形大小 (宽, 高 英寸)
        'figsize_double': (24, 8),         # 并排热图的图形大小 (宽, 高 英寸)
        'dpi': 300,                        # 图像分辨率 (每英寸点数)
    }
    # ------------------

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
        analyze_and_visualize_data(all_patient_data, num_patients, config)
        print("Analysis complete based on configuration.")