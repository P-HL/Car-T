"""
命令行参数解析模块
处理所有命令行参数的解析逻辑
"""

import argparse


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='CAR-T治疗临床数据处理系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 动态数据处理 - 默认验证模式
  python data_processed.py --mode dynamic
  
  # 动态数据处理 - 指定输入和输出目录
  python data_processed.py --mode dynamic --input-dir /path/to/input --output-dir /path/to/output
  
  # 动态数据处理 - 使用配置文件
  python data_processed.py --mode dynamic --config config.yaml
  
  # 动态数据处理 - 启用列删除功能
  python data_processed.py --mode dynamic --enable-column-deletion --validation-only
  
  # 动态数据处理 - 只运行处理步骤
  python data_processed.py --mode dynamic --processing-only
  
  # 静态数据处理
  python data_processed.py --mode static --config config.yaml
  
  # 静态数据处理模式
  python data_processed.py --mode static --input input.csv --output output.csv

环境变量:
  # 动态数据配置
  CART_DYNAMIC_EXPECTED_FILE_COUNT    动态数据预期文件数量
  CART_DYNAMIC_EXPECTED_ROW_COUNT     动态数据预期行数
  CART_DYNAMIC_VALIDATION_ONLY        动态数据只运行验证步骤 (true/false)
  CART_DYNAMIC_PROCESSING_ONLY        动态数据只运行处理步骤 (true/false)
  CART_DYNAMIC_VALIDATION_REPORT      动态数据验证报告文件路径
  CART_DYNAMIC_PROCESSING_REPORT      动态数据处理报告文件路径
  
  # 静态数据配置
  CART_STATIC_VALIDATION_ONLY         静态数据只运行验证步骤 (true/false)
  CART_STATIC_PROCESSING_ONLY         静态数据只运行处理步骤 (true/false)
  CART_STATIC_EXPECTED_COLUMN_COUNT   静态数据预期列数
  CART_STATIC_EXPECTED_PATIENT_COUNT  静态数据预期患者数
  
  # 通用配置
  CART_INPUT_DIR                      动态数据输入目录路径
  CART_OUTPUT_DIR                     动态数据输出目录路径
  CART_STATIC_INPUT_FILE              静态处理输入文件路径
  CART_STATIC_OUTPUT_FILE             静态处理输出文件路径
  CART_REMOVE_OPTIONAL                是否删除可选列 (true/false)
  CART_VERBOSE                        是否显示详细信息 (true/false)
  CART_PROGRESS_INTERVAL              进度显示间隔
  CART_SKIP_INTERACTIVE               跳过交互式询问 (true/false)
        """
    )
    
    # 处理模式选择（强制要求）
    parser.add_argument('--mode', choices=['dynamic', 'static'], required=True,
                       help='选择处理模式: dynamic (动态数据处理) 或 static (静态数据处理)')
    
    # 路径配置（已移至配置文件）
    parser.add_argument('--input-dir', dest='input_dir',
                       help='输入数据目录路径（覆盖配置文件）')
    parser.add_argument('--output-dir', dest='output_dir',
                       help='输出数据目录路径（覆盖配置文件）')
    
    # 数据验证配置
    parser.add_argument('--dynamic-expected-file-count', dest='dynamic_expected_file_count', type=int,
                       help='动态数据预期文件数量')
    parser.add_argument('--dynamic-expected-row-count', dest='dynamic_expected_row_count', type=int,
                       help='动态数据预期行数')
    
    # 处理配置
    parser.add_argument('--enable-column-deletion', dest='enable_column_deletion',
                       action='store_true', help='启用列删除功能')
    parser.add_argument('--no-verbose', dest='verbose', action='store_false',
                       help='不显示详细信息')
    parser.add_argument('--progress-interval', dest='progress_interval', type=int,
                       help='进度显示间隔')
    
    # 输出配置
    parser.add_argument('--dynamic-validation-report', dest='dynamic_validation_report_path',
                       help='动态数据验证报告文件路径')
    parser.add_argument('--dynamic-processing-report', dest='dynamic_processing_report_path',
                       help='动态数据处理报告文件路径')
    
    # 配置文件
    parser.add_argument('--config', dest='config_file',
                       help='YAML配置文件路径')
    
    # 步骤控制
    parser.add_argument('--validation-only', dest='dynamic_validation_only', action='store_true',
                       help='只运行数据验证步骤')
    parser.add_argument('--processing-only', dest='dynamic_processing_only', action='store_true',
                       help='只运行数据处理步骤')
    parser.add_argument('--skip-interactive', dest='skip_interactive', action='store_true',
                       help='跳过交互式询问，使用配置值')
    
    # 实用功能
    parser.add_argument('--create-sample-config', action='store_true',
                       help='创建示例配置文件并退出')
    parser.add_argument('--print-config', action='store_true',
                       help='打印当前配置并退出')
    
    # 检查是否是工具命令（不需要--mode参数）
    import sys
    tool_commands = ['--create-sample-config', '--print-config']
    if any(cmd in sys.argv for cmd in tool_commands):
        # 临时移除--mode的required属性
        for action in parser._actions:
            if action.dest == 'mode':
                action.required = False
                break
    
    return parser.parse_args()
