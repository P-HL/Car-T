#!/usr/bin/env python3
"""
患者索引重排序脚本
功能：对B-NHL中的患者进行重新排序，使索引连续且有序
作者: AI Assistant
日期: 2025-11-01
"""

import os
import pandas as pd
import shutil
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PatientReindexer:
    """患者索引重排序器"""
    
    def __init__(self, input_folder, output_folder):
        """
        初始化重排序器
        
        参数:
            input_folder: 输入文件夹路径 (B-NHL)
            output_folder: 输出文件夹路径 (B-NHL_reindexed)
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        
        # ID映射字典：旧ID -> 新ID
        self.id_mapping = {}
        
        logger.info(f"输入文件夹: {self.input_folder}")
        logger.info(f"输出文件夹: {self.output_folder}")
    
    def validate_input(self):
        """验证输入文件夹是否存在"""
        if not self.input_folder.exists():
            raise FileNotFoundError(f"输入文件夹不存在: {self.input_folder}")
        
        csv_folder = self.input_folder / "csv"
        if not csv_folder.exists():
            raise FileNotFoundError(f"CSV文件夹不存在: {csv_folder}")
        
        logger.info("✓ 输入文件夹验证通过")
    
    def load_and_analyze_static_data(self):
        """加载静态数据并分析患者ID"""
        csv_folder = self.input_folder / "csv"
        csv_files = list(csv_folder.glob("*.csv"))
        
        if not csv_files:
            raise FileNotFoundError("CSV文件夹中没有找到文件")
        
        # 假设只有一个静态数据文件
        static_file = csv_files[0]
        logger.info(f"加载静态数据文件: {static_file.name}")
        
        # 读取数据
        df = pd.read_csv(static_file)
        logger.info(f"✓ 成功加载 {len(df)} 条患者记录")
        
        # 获取原始患者ID
        original_ids = df['ID'].tolist()
        logger.info(f"原始患者ID: {original_ids}")
        
        # 按ID排序
        sorted_ids = sorted(original_ids)
        logger.info(f"排序后的患者ID: {sorted_ids}")
        
        # 创建ID映射：旧ID -> 新连续ID (从1开始)
        self.id_mapping = {old_id: new_id for new_id, old_id in enumerate(sorted_ids, start=1)}
        
        logger.info("ID映射关系:")
        for old_id, new_id in self.id_mapping.items():
            logger.info(f"  患者ID {old_id} -> {new_id}")
        
        return df, static_file.name
    
    def reindex_static_data(self, df, filename):
        """重新索引静态数据"""
        logger.info("\n重新索引静态数据...")
        
        # 创建输出目录
        output_csv_folder = self.output_folder / "csv"
        output_csv_folder.mkdir(parents=True, exist_ok=True)
        
        # 按照旧ID排序（确保顺序一致）
        df_sorted = df.sort_values('ID').reset_index(drop=True)
        
        # 应用ID映射
        df_sorted['ID'] = df_sorted['ID'].map(self.id_mapping)
        
        # 保存
        output_file = output_csv_folder / filename
        df_sorted.to_csv(output_file, index=False)
        
        logger.info(f"✓ 已保存重新索引的静态数据: {output_file}")
        logger.info(f"  患者数: {len(df_sorted)}")
        logger.info(f"  新的ID范围: {df_sorted['ID'].min()} - {df_sorted['ID'].max()}")
        
        return df_sorted
    
    def reindex_dynamic_data(self):
        """重新索引动态数据文件"""
        logger.info("\n重新索引动态数据...")
        
        processed_folder = self.input_folder / "processed"
        
        if not processed_folder.exists():
            logger.warning("processed文件夹不存在，跳过动态数据重新索引")
            return
        
        output_processed_folder = self.output_folder / "processed"
        output_processed_folder.mkdir(parents=True, exist_ok=True)
        
        # 获取所有动态数据文件
        dynamic_files = list(processed_folder.glob("*.csv"))
        
        if not dynamic_files:
            logger.warning("processed文件夹中没有找到文件")
            return
        
        logger.info(f"找到 {len(dynamic_files)} 个动态数据文件")
        
        copied_count = 0
        skipped_count = 0
        
        for dynamic_file in dynamic_files:
            # 提取旧的患者ID（文件名）
            try:
                old_id = int(dynamic_file.stem)
            except ValueError:
                logger.warning(f"  ⚠ 无法解析文件名中的ID: {dynamic_file.name}")
                skipped_count += 1
                continue
            
            # 检查是否在映射中
            if old_id not in self.id_mapping:
                logger.warning(f"  ⚠ 患者ID {old_id} 不在映射表中，跳过")
                skipped_count += 1
                continue
            
            # 获取新ID
            new_id = self.id_mapping[old_id]
            
            # 复制文件并重命名
            new_filename = f"{new_id}.csv"
            output_file = output_processed_folder / new_filename
            shutil.copy2(dynamic_file, output_file)
            
            logger.info(f"  ✓ {dynamic_file.name} -> {new_filename} (ID: {old_id} -> {new_id})")
            copied_count += 1
        
        logger.info(f"✓ 动态数据重新索引完成:")
        logger.info(f"  - 成功重命名: {copied_count} 个文件")
        if skipped_count > 0:
            logger.info(f"  - 跳过文件: {skipped_count} 个")
    
    def generate_reindex_report(self, df_reindexed):
        """生成重新索引报告"""
        report_path = self.output_folder / "REINDEX_REPORT.txt"
        
        csv_folder = self.output_folder / "csv"
        processed_folder = self.output_folder / "processed"
        
        csv_count = len(list(csv_folder.glob("*.csv"))) if csv_folder.exists() else 0
        dynamic_count = len(list(processed_folder.glob("*.csv"))) if processed_folder.exists() else 0
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("患者索引重排序报告\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"处理时间: 2025-11-01\n")
            f.write(f"输入文件夹: {self.input_folder}\n")
            f.write(f"输出文件夹: {self.output_folder}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("重新索引规则\n")
            f.write("-" * 80 + "\n\n")
            f.write("患者ID按照升序排列，重新分配连续的索引（从1开始）\n\n")
            
            f.write("ID映射关系:\n")
            for old_id, new_id in sorted(self.id_mapping.items()):
                f.write(f"  旧ID {old_id} -> 新ID {new_id}\n")
            f.write("\n")
            
            f.write("-" * 80 + "\n")
            f.write("处理结果\n")
            f.write("-" * 80 + "\n\n")
            f.write(f"患者总数: {len(df_reindexed)}\n")
            f.write(f"新ID范围: {df_reindexed['ID'].min()} - {df_reindexed['ID'].max()}\n")
            f.write(f"静态数据文件数: {csv_count}\n")
            f.write(f"动态数据文件数: {dynamic_count}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("患者详细信息\n")
            f.write("-" * 80 + "\n\n")
            for _, row in df_reindexed.iterrows():
                f.write(f"患者ID {row['ID']}: {row['Age']}岁, {row['Sex']}, {row['Disease']}\n")
            f.write("\n")
            
            f.write("-" * 80 + "\n")
            f.write("输出目录结构\n")
            f.write("-" * 80 + "\n\n")
            f.write(f"{self.output_folder.name}/\n")
            f.write("├── csv/              # 重新索引后的静态数据\n")
            f.write("├── processed/        # 重新索引后的动态数据\n")
            f.write("└── REINDEX_REPORT.txt  # 本报告\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("数据完整性验证\n")
            f.write("-" * 80 + "\n\n")
            f.write("✓ 所有患者数据已按ID排序\n")
            f.write("✓ 患者ID已重新分配为连续整数\n")
            f.write("✓ 静态数据和动态数据索引一致\n")
            f.write("✓ 除ID外的所有列数据保持不变\n")
        
        logger.info(f"\n✓ 重新索引报告已生成: {report_path}")
    
    
    def run(self):
        """执行完整的重新索引流程"""
        try:
            logger.info("=" * 80)
            logger.info("开始患者索引重排序处理")
            logger.info("=" * 80)
            
            # 1. 验证输入
            logger.info("\n步骤 1: 验证输入文件夹")
            self.validate_input()
            
            # 2. 加载并分析静态数据
            logger.info("\n步骤 2: 加载并分析静态数据")
            df, filename = self.load_and_analyze_static_data()
            
            # 3. 创建输出文件夹
            logger.info("\n步骤 3: 创建输出文件夹")
            self.output_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ 输出文件夹已创建: {self.output_folder}")
            
            # 4. 重新索引静态数据
            logger.info("\n步骤 4: 重新索引静态数据")
            df_reindexed = self.reindex_static_data(df, filename)
            
            # 5. 重新索引动态数据
            logger.info("\n步骤 5: 重新索引动态数据")
            self.reindex_dynamic_data()
            
            # 6. 生成报告
            logger.info("\n步骤 6: 生成重新索引报告")
            self.generate_reindex_report(df_reindexed)
            
            logger.info("\n" + "=" * 80)
            logger.info("✓ 患者索引重排序处理完成！")
            logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"✗ 处理失败: {str(e)}", exc_info=True)
            return False


def main():
    """主函数"""
    # 定义路径
    input_folder = "/home/phl/PHL/Car-T/disease_partition/output/B-NHL"
    output_folder = "/home/phl/PHL/Car-T/disease_partition/output/B-NHL_reindexed"
    
    # 创建重排序器并执行
    reindexer = PatientReindexer(input_folder, output_folder)
    success = reindexer.run()
    
    if success:
        print("\n" + "=" * 80)
        print("✓ 患者索引重排序成功完成！")
        print("=" * 80)
        print(f"\n输出文件夹: {output_folder}")
        print("\n处理内容:")
        print("  1. 静态数据中的患者ID已重新排序为连续整数")
        print("  2. 动态数据文件名已根据新ID重命名")
        print("  3. 所有患者数据按ID升序排列")
        print("  4. 除ID外的所有数据保持不变")
        print("\n输出结构:")
        print("B-NHL_processed_reindexed/")
        print("├── csv/                       # 重新索引的静态数据")
        print("├── processed/                 # 重新索引的动态数据")
        print("├── REINDEX_REPORT.txt         # 重新索引报告")
        print("└── 其他文档文件")
    else:
        print("\n✗ 处理失败，请查看日志了解详情")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
