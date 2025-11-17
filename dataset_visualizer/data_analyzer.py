#!/usr/bin/env python3
"""
Data Analyzer Module
数据分析模块

This module contains the StaticDataAnalyzer class for processing 
static clinical data and generating comprehensive analysis reports.
本模块包含StaticDataAnalyzer类，用于处理静态临床数据并生成综合分析报告。
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
import logging

# Configure logging for this module  
logger = logging.getLogger(__name__)


class StaticDataAnalyzer:
    """
    Static data analyzer for categorical variables in clinical data.
    静态数据分析器，用于临床数据中的分类变量分析。
    
    This class provides comprehensive analysis capabilities for static clinical data,
    including demographic analysis, disease characteristics, treatment history,
    CAR-T characteristics, adverse events, and data quality assessment.
    """
    
    def __init__(self, config_manager: Any) -> None:
        """
        Initialize the analyzer with configuration.
        使用配置初始化分析器。
        
        Args:
            config_manager: ConfigManager instance for accessing configuration
        """
        self.config = config_manager
        self.df: Optional[pd.DataFrame] = None
        self.total_patients: int = 0
    
    def load_data(self) -> bool:
        """
        Load data from the configured input file.
        从配置的输入文件加载数据。
        
        Returns:
            True if data loaded successfully, False otherwise
            
        Raises:
            FileNotFoundError: If input file cannot be found
            pd.errors.EmptyDataError: If input file is empty
            pd.errors.ParserError: If input file cannot be parsed
        """
        input_file = self.config.get_path('input_file')
        try:
            self.df = pd.read_csv(input_file)
            self.total_patients = len(self.df)
            logger.info(f"Successfully loaded data from: {input_file}")
            logger.info(f"Total patients: {self.total_patients}")
            print(f"Successfully loaded data from: {input_file}")
            print(f"Total patients: {self.total_patients}")
            return True
        except FileNotFoundError as e:
            error_msg = f"Input file not found: {input_file}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            return False
        except pd.errors.EmptyDataError as e:
            error_msg = f"Input file is empty: {input_file}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Error reading input file {input_file}: {e}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            return False
    
    def analyze_categorical_variables(self) -> None:
        """
        Analyze all categorical variables in the static data table and generate comprehensive report.
        分析静态数据表中的所有分类变量并生成全面报告。
        
        This method orchestrates the complete analysis workflow, generating sections
        for demographics, disease characteristics, treatment history, CAR-T characteristics,
        adverse events, and data quality.
        """
        if self.df is None:
            logger.error("No data loaded. Call load_data() first.")
            print("Error: No data loaded. Call load_data() first.")
            return
        
        # Print column information for debugging
        logger.info(f"Available data columns: {list(self.df.columns)}")
        logger.info(f"Dataset shape: {self.df.shape}")
        print("可用数据列:", list(self.df.columns))
        print("数据集形状:", self.df.shape)
        
        # Generate report header
        report_lines = self._generate_report_header()
        
        # Print to console
        for line in report_lines:
            print(line)
        
        # Generate analysis sections
        sections = [
            self._analyze_demographics(),
            self._analyze_disease_characteristics(), 
            self._analyze_treatment_history(),
            self._analyze_cart_characteristics(),
            self._analyze_adverse_events(),
            self._analyze_data_quality()
        ]
        
        # Print and collect all sections
        for section in sections:
            for line in section:
                print(line)
                report_lines.append(line)
        
        # Save complete report
        self._save_report(report_lines)
    
    def _generate_report_header(self) -> List[str]:
        """
        Generate report header with basic information.
        生成包含基本信息的报告头部。
        
        Returns:
            List of header lines
        """
        header_lines = [
            "=" * 80,
            "血液疾病临床预测项目 - 全面分类变量统计分析报告",
            "Blood Disease Clinical Prediction Project - Comprehensive Categorical Variables Analysis",
            "=" * 80,
            f"生成时间 Generation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"数据源文件 Data Source: encoded.csv", 
            f"数据集总样本量 Total Sample Size: {self.total_patients} 名患者",
            "=" * 80
        ]
        return header_lines
    
    def _analyze_demographics(self) -> List[str]:
        """
        Analyze basic demographic variables.
        分析基本人口统计学变量。
        
        Returns:
            List of analysis result lines
        """
        section = [
            "\n第一部分：基本人口统计学分析 PART I: BASIC DEMOGRAPHICS",
            "=" * 60
        ]
        
        # Analyze sex distribution
        section.extend(self._analyze_sex_distribution())
        
        # Analyze age distribution  
        section.extend(self._analyze_age_distribution())
        
        return section
    
    def _analyze_sex_distribution(self) -> List[str]:
        """
        Analyze sex distribution in the dataset.
        分析数据集中的性别分布。
        
        Returns:
            List of sex analysis lines
        """
        lines = [
            "\n1.1 性别分布 (Sex Distribution)",
            "-" * 40
        ]
        
        if 'Sex' not in self.df.columns:
            lines.append("性别数据不可用 Sex data not available")
            return lines
            
        sex_counts = self.df['Sex'].value_counts()
        for sex, count in sex_counts.items():
            percentage = (count / self.total_patients) * 100
            lines.append(f"{sex}: {count} 名患者 ({percentage:.1f}%)")
        
        # Calculate male:female ratio if applicable
        if len(sex_counts) >= 2:
            male_count = sex_counts.get('male', 0)
            female_count = sex_counts.get('female', 0)
            if female_count > 0:
                ratio = male_count / female_count
                lines.append(f"男女比例 Male:Female Ratio: {ratio:.1f}:1")
        
        return lines
    
    def _analyze_age_distribution(self) -> List[str]:
        """
        Analyze age distribution and grouping.
        分析年龄分布和分组。
        
        Returns:
            List of age analysis lines
        """
        age_threshold = self.config.get('analysis', 'age_threshold', 65)
        lines = [
            f"\n1.2 年龄分布 (Age Distribution) - 以{age_threshold}岁为分界",
            "-" * 40
        ]
        
        if 'Age' not in self.df.columns:
            lines.append("年龄数据不可用 Age data not available")
            return lines
        
        # Basic age statistics
        age_data = self.df['Age'].dropna()
        if len(age_data) == 0:
            lines.append("无有效年龄数据 No valid age data")
            return lines
            
        age_stats = age_data.describe()
        lines.extend([
            f"年龄统计摘要 Age Statistics:",
            f"  平均年龄 Mean: {age_stats['mean']:.1f} 岁",
            f"  中位数 Median: {age_stats['50%']:.1f} 岁", 
            f"  标准差 Std Dev: {age_stats['std']:.1f}",
            f"  最小年龄 Min: {age_stats['min']:.0f} 岁",
            f"  最大年龄 Max: {age_stats['max']:.0f} 岁"
        ])
        
        # Age grouping analysis
        self.df['Age_Group'] = self.df['Age'].apply(
            lambda x: f'< {age_threshold}岁' if x < age_threshold else f'≥ {age_threshold}岁'
        )
        age_group_counts = self.df['Age_Group'].value_counts()
        lines.append(f"\n年龄分组分布 Age Group Distribution:")
        for group, count in age_group_counts.items():
            percentage = (count / self.total_patients) * 100
            lines.append(f"  {group}: {count} 名患者 ({percentage:.1f}%)")
        
        return lines
    
    def _analyze_disease_characteristics(self) -> List[str]:
        """
        Analyze disease-related categorical variables.
        分析疾病相关的分类变量。
        
        Returns:
            List of disease analysis lines
        """
        section = [
            "\n\n第二部分：疾病特征分析 PART II: DISEASE CHARACTERISTICS", 
            "=" * 60
        ]
        
        # Analyze different disease characteristics
        disease_analyses = [
            self._analyze_disease_types(),
            self._analyze_bm_disease_burden(),
            self._analyze_bone_marrow_cellularity(),
            self._analyze_extramedullary_disease(),
            self._analyze_disease_staging()
        ]
        
        for analysis in disease_analyses:
            section.extend(analysis)
        
        return section
    
    def _analyze_disease_types(self) -> List[str]:
        """Analyze disease type distribution."""
        lines = [
            "\n2.1 疾病类型分布 (Disease Distribution)",
            "-" * 40
        ]
        
        if 'Disease' not in self.df.columns:
            lines.append("疾病类型数据不可用 Disease type data not available")
            return lines
            
        disease_counts = self.df['Disease'].value_counts()
        lines.append(f"疾病类型数量 Number of Disease Types: {len(disease_counts)}")
        for disease, count in disease_counts.items():
            percentage = (count / self.total_patients) * 100
            lines.append(f"  {disease}: {count} 名患者 ({percentage:.1f}%)")
        
        return lines
    
    def _analyze_bm_disease_burden(self) -> List[str]:
        """Analyze bone marrow disease burden."""
        lines = [
            "\n2.2 骨髓疾病负荷 (BM Disease Burden)",
            "-" * 40
        ]
        
        if 'BM disease burden' not in self.df.columns:
            lines.append("骨髓疾病负荷数据不可用 BM disease burden data not available")
            return lines
            
        bm_burden = self.df['BM disease burden'].dropna()
        if len(bm_burden) == 0:
            lines.append("无有效骨髓疾病负荷数据 No valid BM disease burden data")
            return lines
        
        # Handle numeric data
        if pd.api.types.is_numeric_dtype(bm_burden):
            bm_stats = bm_burden.describe()
            lines.extend([
                f"骨髓疾病负荷统计 BM Disease Burden Statistics:",
                f"  平均值 Mean: {bm_stats['mean']:.2f}%",
                f"  中位数 Median: {bm_stats['50%']:.2f}%",
                f"  标准差 Std Dev: {bm_stats['std']:.2f}",
                f"  最小值 Min: {bm_stats['min']:.2f}%",
                f"  最大值 Max: {bm_stats['max']:.2f}%"
            ])
            
            # Categorize burden levels
            def categorize_bm_burden(value: float) -> str:
                if value == 0:
                    return "无负荷 (0%)"
                elif value <= 25:
                    return "低负荷 (1-25%)"
                elif value <= 50:
                    return "中负荷 (26-50%)"
                elif value <= 75:
                    return "高负荷 (51-75%)"
                else:
                    return "极高负荷 (>75%)"
            
            self.df['BM_Burden_Category'] = bm_burden.apply(categorize_bm_burden)
            burden_counts = self.df['BM_Burden_Category'].value_counts()
            lines.append(f"\n骨髓疾病负荷分组 BM Disease Burden Categories:")
            for category, count in burden_counts.items():
                percentage = (count / self.total_patients) * 100
                lines.append(f"  {category}: {count} 名患者 ({percentage:.1f}%)")
        
        return lines
    
    def _analyze_bone_marrow_cellularity(self) -> List[str]:
        """Analyze bone marrow cellularity."""
        lines = [
            "\n2.3 骨髓细胞活性 (Bone Marrow Cellularity)",
            "-" * 40
        ]
        
        if 'Bone marrow cellularity' not in self.df.columns:
            lines.append("骨髓细胞活性数据不可用 Bone marrow cellularity data not available")
            return lines
            
        cellularity_counts = self.df['Bone marrow cellularity'].value_counts()
        for cellularity, count in cellularity_counts.items():
            percentage = (count / self.total_patients) * 100
            lines.append(f"  {cellularity}: {count} 名患者 ({percentage:.1f}%)")
        
        return lines
    
    def _analyze_extramedullary_disease(self) -> List[str]:
        """Analyze extramedullary disease features."""
        lines = [
            "\n2.4 髓外病变特征 (Extramedullary Disease Features)",
            "-" * 40
        ]
        
        extramedullary_vars = ['extramedullary mass', 'extranodal involvement', 'B symptoms']
        for var in extramedullary_vars:
            if var in self.df.columns:
                lines.append(f"\n{var}:")
                var_counts = self.df[var].value_counts()
                for value, count in var_counts.items():
                    percentage = (count / self.total_patients) * 100
                    lines.append(f"  {value}: {count} 名患者 ({percentage:.1f}%)")
            else:
                lines.append(f"\n{var}: 数据不可用 Data not available")
        
        return lines
    
    def _analyze_disease_staging(self) -> List[str]:
        """Analyze Ann Arbor disease staging."""
        lines = [
            "\n2.5 Ann Arbor分期 (Ann Arbor Staging)",
            "-" * 40
        ]
        
        if 'Ann Arbor stage' not in self.df.columns:
            lines.append("Ann Arbor分期数据不可用 Ann Arbor staging data not available")
            return lines
            
        stage_counts = self.df['Ann Arbor stage'].value_counts()
        for stage, count in stage_counts.items():
            percentage = (count / self.total_patients) * 100
            lines.append(f"  Stage {stage}: {count} 名患者 ({percentage:.1f}%)")
        
        return lines
    
    def _analyze_treatment_history(self) -> List[str]:
        """
        Analyze treatment history variables.
        分析治疗历史变量。
        
        Returns:
            List of treatment history analysis lines
        """
        section = [
            "\n\n第三部分：治疗历史分析 PART III: TREATMENT HISTORY",
            "=" * 60
        ]
        
        # Analyze different treatment history aspects
        treatment_analyses = [
            self._analyze_prior_therapy_lines(),
            self._analyze_prior_hsct(),
            self._analyze_prior_cart(),
            self._analyze_bridging_therapy()
        ]
        
        for analysis in treatment_analyses:
            section.extend(analysis)
        
        return section
    
    def _analyze_prior_therapy_lines(self) -> List[str]:
        """Analyze number of prior therapy lines."""
        lines = [
            "\n3.1 既往治疗线数 (Number of Prior Therapy Lines)",
            "-" * 40
        ]
        
        col_name = 'Number of prior therapy lines'
        if col_name not in self.df.columns:
            lines.append("既往治疗线数数据不可用 Prior therapy lines data not available")
            return lines
            
        therapy_lines = self.df[col_name].dropna()
        if len(therapy_lines) == 0:
            lines.append("无有效既往治疗线数数据 No valid prior therapy lines data")
            return lines
            
        therapy_stats = therapy_lines.describe()
        lines.extend([
            f"既往治疗线数统计 Prior Therapy Lines Statistics:",
            f"  平均线数 Mean: {therapy_stats['mean']:.1f}",
            f"  中位数 Median: {therapy_stats['50%']:.1f}",
            f"  标准差 Std Dev: {therapy_stats['std']:.1f}",
            f"  最少线数 Min: {therapy_stats['min']:.0f}",
            f"  最多线数 Max: {therapy_stats['max']:.0f}"
        ])
        
        therapy_line_counts = therapy_lines.value_counts().sort_index()
        lines.append(f"\n治疗线数分布 Distribution by Number of Lines:")
        for lines_count, patient_count in therapy_line_counts.items():
            percentage = (patient_count / self.total_patients) * 100
            lines.append(f"  {lines_count} 线: {patient_count} 名患者 ({percentage:.1f}%)")
        
        return lines
    
    def _analyze_prior_hsct(self) -> List[str]:
        """Analyze prior hematopoietic stem cell transplant history.""" 
        lines = [
            "\n3.2 既往造血干细胞移植史 (Prior Hematopoietic Stem Cell Transplant)",
            "-" * 40
        ]
        
        col_name = 'Prior hematopoietic stem cell'
        if col_name not in self.df.columns:
            lines.append("既往干细胞移植数据不可用 Prior HSCT data not available")
            return lines
            
        hsct_counts = self.df[col_name].value_counts()
        for hsct_type, count in hsct_counts.items():
            percentage = (count / self.total_patients) * 100
            lines.append(f"  {hsct_type}: {count} 名患者 ({percentage:.1f}%)")
        
        return lines
    
    def _analyze_prior_cart(self) -> List[str]:
        """Analyze prior CAR-T therapy history."""
        lines = [
            "\n3.3 既往CAR-T治疗史 (Prior CAR-T Therapy)",
            "-" * 40
        ]
        
        col_name = 'Prior CAR-T therapy'
        if col_name not in self.df.columns:
            lines.append("既往CAR-T治疗数据不可用 Prior CAR-T therapy data not available")
            return lines
            
        prior_cart_counts = self.df[col_name].value_counts()
        for status, count in prior_cart_counts.items():
            percentage = (count / self.total_patients) * 100
            lines.append(f"  {status}: {count} 名患者 ({percentage:.1f}%)")
        
        return lines
    
    def _analyze_bridging_therapy(self) -> List[str]:
        """Analyze bridging therapy usage."""
        lines = [
            "\n3.4 桥接治疗 (Bridging Therapy)",
            "-" * 40
        ]
        
        col_name = 'Bridging therapy'
        if col_name not in self.df.columns:
            lines.append("桥接治疗数据不可用 Bridging therapy data not available")
            return lines
            
        bridging_counts = self.df[col_name].value_counts()
        for status, count in bridging_counts.items():
            percentage = (count / self.total_patients) * 100
            lines.append(f"  {status}: {count} 名患者 ({percentage:.1f}%)")
        
        return lines
    
    def _analyze_cart_characteristics(self) -> List[str]:
        """
        Analyze CAR-T treatment characteristics.
        分析CAR-T治疗特征。
        
        Returns:
            List of CAR-T characteristics analysis lines
        """
        section = [
            "\n\n第四部分：CAR-T治疗特征分析 PART IV: CAR-T TREATMENT CHARACTERISTICS",
            "=" * 60
        ]
        
        cart_variables = [
            ('Costimulatory molecule', '4.1 共刺激分子 (Costimulatory Molecule)'),
            ('Type of construct(tandem/single target)', '4.2 构建体类型 (Type of Construct)'),
            ('CAR-T therapy following auto-HSCT', '4.3 自体移植后CAR-T治疗 (CAR-T Therapy Following Auto-HSCT)')
        ]
        
        for var, title in cart_variables:
            section.append(f"\n{title}")
            section.append("-" * 40)
            
            if var in self.df.columns:
                var_counts = self.df[var].value_counts()
                for value, count in var_counts.items():
                    percentage = (count / self.total_patients) * 100
                    section.append(f"  {value}: {count} 名患者 ({percentage:.1f}%)")
            else:
                section.append(f"{var}数据不可用 {var} data not available")
        
        return section
    
    def _analyze_adverse_events(self) -> List[str]:
        """
        Analyze adverse events and complications.
        分析不良事件和并发症。
        
        Returns:
            List of adverse events analysis lines
        """
        section = [
            "\n\n第五部分：不良事件分析 PART V: ADVERSE EVENTS ANALYSIS",
            "=" * 60
        ]
        
        adverse_event_vars = ['CRS grade', 'ICANS grade', 'Early ICAHT grade', 'Late ICAHT grade', 'Infection grade']
        
        for i, var in enumerate(adverse_event_vars, 1):
            section.append(f"\n5.{i} {var}")
            section.append("-" * 40)
            
            if var not in self.df.columns:
                section.append(f"{var}数据不可用 {var} data not available")
                continue
                
            # Handle missing values
            var_data = self.df[var].dropna()
            if len(var_data) == 0:
                section.append("无有效数据 No valid data available")
                continue
                
            # Statistics for each grade
            grade_counts = var_data.value_counts().sort_index()
            section.extend([
                f"有效数据 Valid Data: {len(var_data)} 名患者",
                f"缺失数据 Missing Data: {self.total_patients - len(var_data)} 名患者",
                f"\n等级分布 Grade Distribution:"
            ])
            
            for grade, count in grade_counts.items():
                percentage = (count / len(var_data)) * 100
                section.append(f"  等级 {grade}: {count} 名患者 ({percentage:.1f}%)")
            
            # Calculate event rates
            any_grade_count = (var_data > 0).sum()
            any_grade_percentage = (any_grade_count / len(var_data)) * 100
            section.append(f"\n任何等级事件发生率 Any Grade Event Rate: {any_grade_count}/{len(var_data)} ({any_grade_percentage:.1f}%)")
            
            # High grade events (≥3)
            high_grade_count = (var_data >= 3).sum()
            high_grade_percentage = (high_grade_count / len(var_data)) * 100
            section.append(f"高等级事件发生率 (≥3级) High Grade Event Rate: {high_grade_count}/{len(var_data)} ({high_grade_percentage:.1f}%)")
        
        return section
    
    def _analyze_data_quality(self) -> List[str]:
        """
        Analyze data quality and completeness.
        分析数据质量和完整性。
        
        Returns:
            List of data quality analysis lines
        """
        section = []
        section.append("\n\n第六部分：数据质量分析 PART VI: DATA QUALITY ANALYSIS")
        section.append("=" * 60)
        
        # 6.1 数据完整性分析 Data Completeness
        section.append("\n6.1 数据完整性 (Data Completeness)")
        section.append("-" * 40)
        
        total_cells = self.df.shape[0] * self.df.shape[1]
        missing_counts = self.df.isnull().sum()
        total_missing = missing_counts.sum()
        
        section.append(f"数据集维度 Dataset Dimensions: {self.df.shape[0]} 行 × {self.df.shape[1]} 列")
        section.append(f"总单元格数 Total Cells: {total_cells}")
        section.append(f"缺失值总数 Total Missing Values: {total_missing}")
        section.append(f"数据完整率 Data Completeness: {((total_cells - total_missing) / total_cells * 100):.1f}%")
        
        section.append(f"\n各变量缺失情况 Missing Values by Variable:")
        for col, missing_count in missing_counts.items():
            if missing_count > 0:
                missing_percentage = (missing_count / self.total_patients) * 100
                section.append(f"  {col}: {missing_count} ({missing_percentage:.1f}%)")
        
        # 6.2 数据类型分析 Data Types Analysis
        section.append(f"\n6.2 数据类型分析 (Data Types Analysis)")
        section.append("-" * 40)
        
        dtype_counts = self.df.dtypes.value_counts()
        section.append(f"数据类型分布 Data Type Distribution:")
        for dtype, count in dtype_counts.items():
            section.append(f"  {dtype}: {count} 个变量")
        
        # 6.3 唯一值分析 Unique Values Analysis
        section.append(f"\n6.3 变量唯一值分析 (Unique Values Analysis)")
        section.append("-" * 40)
        
        for col in self.df.columns:
            unique_count = self.df[col].nunique()
            unique_percentage = (unique_count / self.total_patients) * 100
            section.append(f"  {col}: {unique_count} 个唯一值 ({unique_percentage:.1f}%)")
        
        return section
    
    def _save_report(self, report_lines: List[str]) -> None:
        """
        Save comprehensive report to file.
        将综合报告保存到文件。
        
        Args:
            report_lines: List of report content lines
            
        Raises:
            OSError: If file cannot be written due to permissions or disk space
        """
        output_dir = self.config.get_path('output_dir')
        report_filename = self.config.get('output', 'report_filename', 'analysis_report.txt')
        encoding = self.config.get('output', 'encoding', 'utf-8')
        
        report_path = os.path.join(output_dir, report_filename)
        try:
            with open(report_path, 'w', encoding=encoding) as f:
                f.write('\n'.join(report_lines))
            logger.info(f"Comprehensive analysis report saved to: {report_path}")
            print(f"\n全面分析报告已保存到 Comprehensive analysis report saved to: {report_path}")
        except OSError as e:
            error_msg = f"Error saving report due to file system issue: {e}"
            logger.error(error_msg)
            print(f"\n保存报告时出错 Error saving report: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error saving report: {e}"
            logger.error(error_msg)
            print(f"\n保存报告时出错 Error saving report: {error_msg}")
