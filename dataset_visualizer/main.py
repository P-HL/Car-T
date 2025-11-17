#!/usr/bin/env python3
"""
Main entry point for the Static Data Analysis and Visualization System
静态数据分析和可视化系统主入口

This script orchestrates the complete analysis and visualization pipeline
for clinical static data, including comprehensive categorical analysis
and grouped visualization generation.
本脚本协调临床静态数据的完整分析和可视化流程，包括综合分类分析和分组可视化生成。
"""

import os
import sys
import logging
from typing import Optional

from config_manager import ConfigManager
from data_analyzer import StaticDataAnalyzer
from data_visualizer import StaticDataVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main() -> bool:
    """
    Main function to run the complete analysis and visualization pipeline.
    主函数，运行完整的分析和可视化流程。
    
    Returns:
        True if pipeline executed successfully, False otherwise
        
    Raises:
        Exception: Any unexpected errors during pipeline execution
    """
    print("=" * 80)
    print("血液疾病临床预测项目 - 静态数据分析系统")
    print("Blood Disease Clinical Prediction Project - Static Data Analysis System")
    print("=" * 80)
    
    try:
        # Initialize configuration manager
        print("\n1. Loading configuration...")
        logger.info("Initializing configuration manager")
        config_manager = ConfigManager()
        
        # Validate configuration
        if not config_manager.validate_config():
            logger.error("Configuration validation failed")
            print("Error: Configuration validation failed. Please check your settings.")
            return False
        
        # Create output directory if it doesn't exist
        output_dir = config_manager.get_path('output_dir')
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory: {output_dir}")
        print(f"Output directory: {output_dir}")
        
        # Initialize and run data analyzer
        if not _run_data_analysis(config_manager):
            return False
        
        # Initialize and run data visualizer
        if not _run_data_visualization(config_manager):
            return False
        
        print("\n" + "=" * 80)
        print("Analysis and visualization completed successfully!")
        print("分析和可视化已成功完成！")
        print("=" * 80)
        
        logger.info("Pipeline completed successfully")
        return True
        
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user")
        print("\nPipeline interrupted by user.")
        return False
    except Exception as e:
        error_msg = f"Error occurred during execution: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"\nError occurred during execution: {e}")
        print(f"执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def _run_data_analysis(config_manager: ConfigManager) -> bool:
    """
    Run the data analysis phase.
    运行数据分析阶段。
    
    Args:
        config_manager: Configuration manager instance
        
    Returns:
        True if analysis completed successfully, False otherwise
    """
    print("\n2. Initializing data analyzer...")
    logger.info("Initializing data analyzer")
    analyzer = StaticDataAnalyzer(config_manager)
    
    # Load and analyze data
    print("\n3. Loading and analyzing data...")
    logger.info("Loading data for analysis")
    if not analyzer.load_data():
        logger.error("Failed to load data for analysis")
        print("Error: Failed to load data. Exiting.")
        return False
    
    # Perform comprehensive analysis
    print("\n4. Performing comprehensive categorical analysis...")
    logger.info("Starting comprehensive categorical analysis")
    analyzer.analyze_categorical_variables()
    logger.info("Categorical analysis completed")
    
    return True


def _run_data_visualization(config_manager: ConfigManager) -> bool:
    """
    Run the data visualization phase.
    运行数据可视化阶段。
    
    Args:
        config_manager: Configuration manager instance
        
    Returns:
        True if visualization completed successfully, False otherwise
    """
    print("\n5. Initializing data visualizer...")
    logger.info("Initializing data visualizer")
    visualizer = StaticDataVisualizer(config_manager)
    
    # Load data into visualizer
    logger.info("Loading data for visualization")
    if not visualizer.load_data():
        logger.error("Failed to load data for visualization")
        print("Error: Failed to load data for visualization. Exiting.")
        return False
    
    # Create comprehensive visualizations
    print("\n6. Creating comprehensive visualizations...")
    logger.info("Creating comprehensive visualizations")
    visualizer.create_comprehensive_visualization()
    
    # Create summary dashboard
    print("\n7. Creating summary dashboard...")
    logger.info("Creating summary dashboard")
    visualizer.create_summary_dashboard()
    logger.info("Visualization phase completed")
    
    return True


if __name__ == "__main__":
    """Entry point when script is run directly."""
    try:
        success = main()
        exit_code = 0 if success else 1
        logger.info(f"Script finished with exit code: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.warning("Script interrupted by user")
        print("\nScript interrupted by user.")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logger.critical(f"Critical error in main execution: {e}", exc_info=True)
        print(f"Critical error: {e}")
        sys.exit(1)
