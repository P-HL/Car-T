	
# 代码解释
    # •	覆盖率热图：0–100% 数据可用率
    # •	缺失率热图：0–100% 缺失率（即 100% - 覆盖率）
    # •	专业化可视化：清晰标签、图例、配色可选（默认白–深蓝渐变，更强对比度）
    # •	灵活导出：支持 PNG、PDF、SVG 等格式
    # •	可配置选项：
        # •	plot_mode: "coverage", "missing", "both", "original"
        # •	output_format: "png", "pdf", "svg"
        # •	color_map: 可选 colormap（例如 "Blues", "YlOrRd", "viridis"）
        # •	fig_size: 控制图像大小（宽, 高）
        # •	dpi: 分辨率
        # •	side_by_side: True 时覆盖率 & 缺失率并排比较；False 时分别输出两张图

# 功能总结
	# •	三种 CSV 输出
        # •	data_availability_fraction.csv (0–1)
        # •	data_availability_percentage.csv (0–100%)
        # •	data_missing_percentage.csv (0–100%)
	# •	双热图可视化
        # •	覆盖率热图
        # •	缺失率热图
        # •	可单独生成或并排对比
	# •	学术出版物适配
        # •	高分辨率 (dpi=300+)
        # •	专业标签、坐标轴、图例
        # •	可选 PNG/PDF/SVG 格式


import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------------
# 配置参数
# ------------------------
CONFIG = {
    "input_folder": "/home/phl/PHL/pytorch-forecasting/datasetcart/processed",
    "output_folder": "/home/phl/PHL/Car-T/heatmap_generator/output_gpt5",
    "plot_mode": "original",   # 可选: "coverage", "missing", "both", "original"
    "output_format": "png", # 可选: "png", "pdf", "svg"
    "color_map": "Blues",   # 可选: "Blues", "YlOrRd", "viridis", etc.
    "fig_size": (14, 6),    # 图像大小
    "dpi": 300,             # 分辨率
    "side_by_side": True    # 是否并排显示覆盖率和缺失率
}

# ------------------------
# 变量分组定义
# ------------------------
CATEGORY_GROUPS = {
    "CBC": [f"CBC{str(i).zfill(3)}" for i in range(1, 25)],
    "Inflammatory Biomarker": [f"Inflammatory Biomarker{str(i).zfill(3)}" for i in range(1, 10)],
    "VCN": ["VCN001"],
    "Lymphocyte Subsets": [f"Lymphocyte Subsets{str(i).zfill(3)}" for i in range(1, 12)],
    "Coagulation": [f"Coagulation{str(i).zfill(3)}" for i in range(1, 9)],
    "Electrolytes": [f"Electrolytes{str(i).zfill(3)}" for i in range(1, 7)],
    "Biochemistry": [f"Biochemistry{str(i).zfill(3)}" for i in range(1, 29)],
    "Vital Signs": [f"Vital Signs{str(i).zfill(3)}" for i in range(1, 7)],
}

# ------------------------
# Step 1: 读取 & 合并数据
# ------------------------
def load_patient_data(input_folder):
    all_files = glob.glob(os.path.join(input_folder, "*.csv"))
    patient_data = []

    for file in all_files:
        df = pd.read_csv(file, index_col=0)
        df.index = df.index.astype(int)
        df = df.loc[-15:30]  # 保证时间范围一致
        patient_data.append(df)
    return patient_data

# ------------------------
# Step 2: 计算可用率矩阵
# ------------------------
def compute_availability_matrix(patient_data):
    all_days = range(-15, 31)
    category_names = list(CATEGORY_GROUPS.keys())

    availability_matrix = pd.DataFrame(0.0, index=category_names, columns=all_days)

    # 遍历所有患者，累积非缺失率
    for df in patient_data:
        for category, variables in CATEGORY_GROUPS.items():
            sub_df = df[variables].notna().astype(int).mean(axis=1)  # 每天该类别的覆盖率
            availability_matrix.loc[category, sub_df.index] += sub_df.values

    # 计算平均覆盖率 (0–1)
    availability_matrix /= len(patient_data)

    return availability_matrix

# ------------------------
# Step 3: 导出 CSV
# ------------------------
def export_csv_files(availability_matrix, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    # 小数版 (0–1)
    availability_matrix.to_csv(os.path.join(output_folder, "data_availability_fraction.csv"))

    # 百分比版 (0–100)
    percentage_matrix = (availability_matrix * 100).round(0).astype(int)
    percentage_matrix.to_csv(os.path.join(output_folder, "data_availability_percentage.csv"))

    # 缺失率百分比 (100 – 可用率)
    missing_matrix = 100 - percentage_matrix
    missing_matrix.to_csv(os.path.join(output_folder, "data_missing_percentage.csv"))

# ------------------------
# Step 4: 绘制热图
# ------------------------
def plot_heatmap(matrix, title, cmap, output_name, config):
    plt.figure(figsize=config["fig_size"], dpi=config["dpi"])
    sns.heatmap(matrix, cmap=cmap, vmin=0, vmax=100,
                cbar_kws={'label': 'Percentage (%)'}, linewidths=0.5, linecolor="grey")

    plt.title(title, fontsize=14, weight="bold")
    plt.xlabel("Days", fontsize=12)
    plt.ylabel("Categories", fontsize=12)

    plt.xticks(
        ticks=np.arange(0.5, len(matrix.columns), 5),
        labels=[str(day) for day in matrix.columns[::5]],
        rotation=0
    )

    plt.tight_layout()
    plt.savefig(f"{config['output_folder']}/{output_name}.{config['output_format']}", dpi=config["dpi"])
    plt.close()

# ------------------------
# Step 5: 主流程
# ------------------------
def main(config):
    patient_data = load_patient_data(config["input_folder"])
    availability_matrix = compute_availability_matrix(patient_data)

    # 导出 CSV
    export_csv_files(availability_matrix, config["output_folder"])

    # 覆盖率矩阵 (%)
    coverage_matrix = (availability_matrix * 100).round(1)
    # 缺失率矩阵 (%)
    missing_matrix = 100 - coverage_matrix

    # 绘图逻辑
    if config["plot_mode"] == "coverage":
        plot_heatmap(coverage_matrix, "Data Coverage Heatmap", config["color_map"], "coverage_heatmap", config)

    elif config["plot_mode"] == "missing":
        plot_heatmap(missing_matrix, "Data Missingness Heatmap", config["color_map"], "missing_heatmap", config)

    elif config["plot_mode"] == "both":
        if config["side_by_side"]:
            fig, axes = plt.subplots(1, 2, figsize=(2 * config["fig_size"][0], config["fig_size"][1]), dpi=config["dpi"])

            sns.heatmap(coverage_matrix, cmap=config["color_map"], vmin=0, vmax=100,
                        cbar_kws={'label': 'Coverage (%)'}, ax=axes[0], linewidths=0.5, linecolor="grey")
            axes[0].set_title("Data Coverage (%)", fontsize=14, weight="bold")
            axes[0].set_xlabel("Days")
            axes[0].set_ylabel("Categories")

            sns.heatmap(missing_matrix, cmap=config["color_map"], vmin=0, vmax=100,
                        cbar_kws={'label': 'Missingness (%)'}, ax=axes[1], linewidths=0.5, linecolor="grey")
            axes[1].set_title("Data Missingness (%)", fontsize=14, weight="bold")
            axes[1].set_xlabel("Days")
            axes[1].set_ylabel("")

            for ax in axes:
                ax.set_xticks(np.arange(0.5, len(coverage_matrix.columns), 5))
                ax.set_xticklabels([str(day) for day in coverage_matrix.columns[::5]], rotation=0)

            plt.tight_layout()
            plt.savefig(f"{config['output_folder']}/coverage_missing_comparison.{config['output_format']}",
                        dpi=config["dpi"])
            plt.close()
        else:
            plot_heatmap(coverage_matrix, "Data Coverage Heatmap", config["color_map"], "coverage_heatmap", config)
            plot_heatmap(missing_matrix, "Data Missingness Heatmap", config["color_map"], "missing_heatmap", config)

    else:
        print("Using original mode (coverage only).")
        plot_heatmap(coverage_matrix, "Data Coverage Heatmap", config["color_map"], "coverage_heatmap", config)


if __name__ == "__main__":
    main(CONFIG)