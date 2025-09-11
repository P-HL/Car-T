import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os

# --- 配置路径 ---
STATIC_DATA_PATH = '/home/phl/PHL/Car-T/datasetcart/encoded.csv'
DYNAMIC_DATA_FOLDER = '/home/phl/PHL/Car-T/datasetcart/processed'
OUTPUT_FOLDER = './output' # 用于保存图表的输出文件夹

# 确保输出文件夹存在
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# --- 1. 静态数据分析 (此部分代码不变) ---

def analyze_static_data(file_path, output_folder):
    """
    分析静态数据中的缺失值并保存图表。
    """
    print("--- 正在分析静态数据 ---")
    try:
        df_static = pd.read_csv(file_path, index_col=0)
    except FileNotFoundError:
        print(f"错误：找不到静态数据文件：{file_path}")
        return
    except Exception as e:
        print(f"读取静态数据时出错: {e}")
        return

    missing_percentage = df_static.isnull().mean() * 100
    missing_count = df_static.isnull().sum()
    total_count = df_static.shape[0]

    missing_info_static = pd.DataFrame({
        'Missing Percentage': missing_percentage,
        'Missing Ratio': [f"{int(missing_count[col])}/{total_count}" for col in df_static.columns]
    })
    missing_info_static.index.name = 'Variable Category'
    missing_info_static = missing_info_static.sort_values(by='Missing Percentage', ascending=False)

    print("静态数据缺失值信息:")
    print(missing_info_static)

    plt.figure(figsize=(20, 8))
    plt.subplot(1, 2, 1)
    sns.barplot(x=missing_info_static.index, y='Missing Percentage', data=missing_info_static, palette='viridis')
    plt.title('Static Data: Missing Value Percentage by Variable Category', fontsize=16)
    plt.xlabel('Variable Category', fontsize=12)
    plt.ylabel('Missing Percentage (%)', fontsize=12)
    plt.xticks(rotation=90, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.subplot(1, 2, 2)
    table_data = missing_info_static.reset_index()
    table_data['Missing Percentage'] = table_data['Missing Percentage'].apply(lambda x: f"{x:.2f}%")
    ax_table = plt.gca()
    ax_table.axis('off')
    table = ax_table.table(cellText=table_data.values,
                            colLabels=table_data.columns,
                            loc='center',
                            cellLoc='center',
                            bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)
    plt.title('Static Data: Missing Value Details', fontsize=16, pad=20)

    plt.suptitle('Static Data Missing Value Analysis', fontsize=20, y=1.02)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    save_path = os.path.join(output_folder, 'static_data_missing_analysis.png')
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    print(f"静态数据分析图表已保存至: {save_path}")
    plt.close()
    print("\n")


# --- 2. 动态数据分析 (修改后的部分) ---

def analyze_dynamic_data_by_category_dual_pane(folder_path, output_folder):
    """
    为每个动态变量类别创建独立的双面板缺失值分析图表（条形图+数据表）。
    """
    print("--- 正在分析动态数据 ---")
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    if not csv_files:
        print("错误：在指定文件夹中未找到动态数据CSV文件。")
        return

    print(f"正在从 {len(csv_files)} 位患者的数据中加载动态数据...")
    all_patient_dfs = [pd.read_csv(os.path.join(folder_path, f), index_col=0) for f in csv_files]
    df_aggregated = pd.concat(all_patient_dfs, ignore_index=True)
    print("所有患者的动态数据已成功合并。")

    variable_groups = {
        "CBC": [f"CBC{i:03d}" for i in range(1, 25)],
        "Inflammatory Biomarker": [f"Inflammatory Biomarker{i:03d}" for i in range(1, 10)],
        "VCN": ["VCN001"],
        "Lymphocyte Subsets": [f"Lymphocyte Subsets{i:03d}" for i in range(1, 12)],
        "Coagulation": [f"Coagulation{i:03d}" for i in range(1, 9)],
        "Electrolytes": [f"Electrolytes{i:03d}" for i in range(1, 7)],
        "Biochemistry": [f"Biochemistry{i:03d}" for i in range(1, 29)],
        "Vital Signs": [f"Vital Signs{i:03d}" for i in range(1, 7)],
    }

    for category_name, var_list in variable_groups.items():
        print(f"\n--- 正在为类别 '{category_name}' 生成图表 ---")
        
        existing_vars = [var for var in var_list if var in df_aggregated.columns]
        if not existing_vars:
            print(f"警告：在数据中未找到类别 '{category_name}' 的任何变量。跳过此类别。")
            continue
        
        df_category = df_aggregated[existing_vars]

        # --- 准备数据 ---
        # 计算缺失值统计数据
        missing_count = df_category.isnull().sum()
        total_count = len(df_category)
        missing_percentage = (missing_count / total_count) * 100

        # 1. 为条形图准备数据（按变量名排序）
        chart_data = missing_percentage.sort_index(ascending=True)

        # 2. 为数据表准备数据（按缺失百分比降序排序）
        table_info = pd.DataFrame({
            'Variable': missing_percentage.index,
            'Missing Percentage': missing_percentage.values,
            'Missing Ratio': [f"{int(missing_count[var])}/{total_count}" for var in missing_percentage.index]
        }).sort_values(by='Missing Percentage', ascending=False)
        
        # --- 创建双面板可视化 ---
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 8))
        fig.suptitle(f'Dynamic Data Missing Value Analysis: {category_name}', fontsize=20)

        # --- 左图：条形图 ---
        sns.barplot(x=chart_data.index, y=chart_data.values, ax=ax1, palette='plasma')
        ax1.set_title(f'Missing Value Percentage by Variable', fontsize=16)
        ax1.set_xlabel("Variable Name", fontsize=12)
        ax1.set_ylabel("Missing Percentage (%)", fontsize=12)
        ax1.grid(axis='y', linestyle='--', alpha=0.7)

        # 调整X轴标签以提高可读性
        tick_spacing = 4 if len(existing_vars) > 10 else 1 # 如果变量少，则显示所有标签
        ax1.xaxis.set_major_locator(mticker.MultipleLocator(tick_spacing))
        ax1.tick_params(axis='x', rotation=45, labelsize=10)

        # --- 右图：数据表 ---
        # 格式化百分比列用于显示
        table_info['Missing Percentage'] = table_info['Missing Percentage'].apply(lambda x: f"{x:.2f}%")
        
        ax2.axis('off')
        ax2.set_title('Missing Value Details (Sorted by %)', fontsize=16, pad=20)
        table = ax2.table(cellText=table_info.values,
                          colLabels=table_info.columns,
                          loc='center',
                          cellLoc='center',
                          bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.2)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95]) # 调整布局以适应总标题

        # --- 保存图表 ---
        safe_category_name = category_name.replace(" ", "_")
        save_path = os.path.join(output_folder, f"dynamic_data_missing_{safe_category_name}.png")
        plt.savefig(save_path, dpi=300)
        print(f"图表已保存至: {save_path}")
        plt.close(fig)


# --- 主执行部分 ---
if __name__ == "__main__":
    # 执行静态数据分析
    analyze_static_data(STATIC_DATA_PATH, OUTPUT_FOLDER)

    # 执行新的双面板动态数据分析
    analyze_dynamic_data_by_category_dual_pane(DYNAMIC_DATA_FOLDER, OUTPUT_FOLDER)