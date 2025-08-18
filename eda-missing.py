"""
eda_workflow.py

CAR-T 项目探索性数据分析 (EDA) 脚本
-------------------------------------
此脚本实现了对静态和动态数据的探索性数据分析，支持生成交互式输出和 PDF 报告。
用户只需修改输入路径，即可直接运行。

运行方式:
    python eda_workflow.py

作者: 你的名字
日期: 2025-08-17
"""

import os
import sys
import logging
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ==============================
# 日志配置
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# ==============================
# 静态数据分析函数
# ==============================
def analyze_static_data(static_file):
    """
    分析静态数据（基线特征、人群学信息等）
    输入:
        static_file: str, 静态数据 CSV 文件路径
    返回:
        (result_dict, figure_list)
    """
    results = {}
    figures = []

    try:
        logging.info(f"加载静态数据: {static_file}")
        df = pd.read_csv(static_file)

        # 缺失值统计
        missing = df.isnull().sum()
        results["missing_values"] = missing

        fig, ax = plt.subplots()
        missing.plot(kind="bar", ax=ax)
        ax.set_title("Missing Values (Static Data)")
        fig_path = "static_missing.png"
        fig.savefig(fig_path)
        plt.close(fig)
        figures.append(fig_path)

        # 描述性统计
        desc = df.describe(include="all")
        results["descriptive_stats"] = desc

        logging.info("静态数据分析完成")
        return results, figures

    except FileNotFoundError:
        logging.error(f"未找到静态数据文件: {static_file}")
        raise
    except Exception as e:
        logging.error(f"静态数据分析出错: {e}")
        raise


# ==============================
# 动态数据分析函数
# ==============================
def analyze_dynamic_data(dynamic_folder):
    """
    分析动态数据（时间序列）
    输入:
        dynamic_folder: str, 存放 pt_x.csv 的文件夹路径
    返回:
        (result_dict, figure_list)
    """
    results = {}
    figures = []

    try:
        logging.info(f"加载动态数据目录: {dynamic_folder}")
        if not os.path.exists(dynamic_folder):
            raise FileNotFoundError(f"动态数据目录不存在: {dynamic_folder}")

        # 简单示例：统计患者文件数
        patient_files = [f for f in os.listdir(dynamic_folder) if f.endswith(".csv")]
        results["num_patients"] = len(patient_files)

        if not patient_files:
            logging.warning("未找到任何动态数据文件")
            return results, figures

        # 示例：分析第一个患者的时间序列
        sample_file = os.path.join(dynamic_folder, patient_files[0])
        df = pd.read_csv(sample_file)

        missing = df.isnull().sum()
        results["sample_missing"] = missing

        fig, ax = plt.subplots()
        missing.plot(kind="bar", ax=ax)
        ax.set_title(f"Missing Values (Example: {patient_files[0]})")
        fig_path = "dynamic_missing.png"
        fig.savefig(fig_path)
        plt.close(fig)
        figures.append(fig_path)

        logging.info("动态数据分析完成")
        return results, figures

    except Exception as e:
        logging.error(f"动态数据分析出错: {e}")
        raise


# ==============================
# PDF 报告生成函数
# ==============================
def generate_pdf_report(static_results, static_figs, dynamic_results, dynamic_figs, output_path="eda_report.pdf"):
    """
    生成 PDF 格式的 EDA 报告
    """
    logging.info(f"正在生成 PDF 报告: {output_path}")
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    # 标题
    story.append(Paragraph("CAR-T EDA 分析报告", styles["Title"]))
    story.append(Spacer(1, 12))

    # 静态数据部分
    story.append(Paragraph("静态数据分析", styles["Heading2"]))
    story.append(Paragraph(f"缺失值统计:<br/>{static_results['missing_values'].to_frame().to_html()}", styles["Normal"]))
    story.append(Spacer(1, 12))
    for fig in static_figs:
        story.append(RLImage(fig, width=400, height=200))
        story.append(Spacer(1, 12))

    # 动态数据部分
    story.append(Paragraph("动态数据分析", styles["Heading2"]))
    story.append(Paragraph(f"患者文件数: {dynamic_results['num_patients']}", styles["Normal"]))
    if "sample_missing" in dynamic_results:
        story.append(Paragraph(f"示例文件缺失值:<br/>{dynamic_results['sample_missing'].to_frame().to_html()}", styles["Normal"]))
    story.append(Spacer(1, 12))
    for fig in dynamic_figs:
        story.append(RLImage(fig, width=400, height=200))
        story.append(Spacer(1, 12))

    doc.build(story)
    logging.info("PDF 报告生成完成")


# ==============================
# 主函数
# ==============================
def main():
    """
    主 EDA 工作流
    用户需在此修改数据路径
    """
    # TODO: 修改为你自己的路径
    static_file = "/home/phl/PHL/pytorch-forecasting/datasetcart/encoded.csv"        # 静态数据 CSV 文件
    dynamic_folder = "/home/phl/PHL/pytorch-forecasting/datasetcart/processed"   # 动态数据文件夹

    try:
        logging.info(">>> 开始执行 CAR-T 项目的 EDA 分析流程...")

        # 静态数据分析
        static_results, static_figs = analyze_static_data(static_file)

        # 动态数据分析
        dynamic_results, dynamic_figs = analyze_dynamic_data(dynamic_folder)

        # 生成 PDF 报告
        generate_pdf_report(static_results, static_figs, dynamic_results, dynamic_figs)

        logging.info(">>> EDA 分析流程完成，报告已保存到 eda_report.pdf")

    except Exception as e:
        logging.error(f"EDA 工作流执行失败: {e}")


# ==============================
# 脚本入口
# ==============================
if __name__ == "__main__":
    main()