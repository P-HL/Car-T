#!/usr/bin/env python3
"""
CAR-T治疗临床数据处理系统 - 模块化版本
==================================================

这是一个重构后的模块化数据处理系统，将原来的单体文件拆分为多个专门的模块：

1. config_manager.py - 配置管理模块
2. cli_parser.py - 命令行参数解析模块
3. dynamic_data_processing/ - 动态数据处理模块包
   - validator.py - 数据验证器
   - processor.py - 数据处理器
   - step_executor.py - 步骤执行器
4. static_data_processing/ - 静态数据处理模块包
   - static_processor.py - 静态数据处理器
   - static_converters.py - 数据转换函数

主要功能:
- 动态患者数据验证和处理
- 静态患者数据标准化编码
- 配置管理和命令行界面
- 模块化架构便于维护和扩展

使用方法:
python data_processed.py [options]

示例:
# 只进行动态数据验证
python data_processed.py --validation-only

# 只进行动态数据处理
python data_processed.py --processing-only

# 进行静态数据处理
python data_processed.py --mode static --input input.csv --output output.csv

# 使用配置文件
python data_processed.py --config config.yaml
"""

import sys
import os

# 添加当前目录到Python路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager, create_sample_config
from utils.cli_parser import parse_arguments
from dynamic_data_processing import StepExecutor
from static_data_processing import StaticDataProcessor


def main():
    """
    主入口函数
    根据用户选择的模式执行相应的数据处理流程
    """
    # 解析命令行参数
    args = parse_arguments()
    
    # 处理实用功能
    if args.create_sample_config:
        create_sample_config()
        print("✅ 示例配置文件已创建")
        return
    
    # 创建配置管理器并加载配置
    config = ConfigManager()
    config.load_from_env()
    
    if hasattr(args, 'config_file') and args.config_file:
        config.load_from_yaml(args.config_file)
    
    config.load_from_args(args)
    
    if hasattr(args, 'print_config') and args.print_config:
        config.print_config()
        return
    
    # 检查处理模式
    processing_mode = getattr(args, 'mode', 'dynamic')
    
    if processing_mode == 'static':
        # 静态数据处理模式 - 使用配置
        handle_static_processing(config, args)
    else:
        # 动态数据处理模式（默认）
        handle_dynamic_processing(config)



def handle_dynamic_processing(config):
    """
    处理动态数据处理流程
    
    Args:
        config: 配置管理器对象
    """
    print("=" * 80)
    print("CAR-T治疗临床数据处理系统 - 动态数据处理模式")
    print("=" * 80)
    
    # 打印配置信息
    if config.get('print_config'):
        config.print_config()
        return
    
    # 验证配置
    try:
        config.validate_config()
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        sys.exit(1)
    
    # 创建并执行步骤
    executor = StepExecutor(config)
    executor.execute_all_steps()


def handle_static_processing(config, args=None):
    """
    处理静态数据处理流程 - 使用配置文件
    
    Args:
        config: 配置管理器对象
        args: 命令行参数对象
    """
    from static_data_processing.static_validator import StaticDataValidator
    from static_data_processing.static_processor import StaticDataProcessor
    
    print("=" * 80)
    print("CAR-T治疗临床数据处理系统 - 静态数据处理模式")
    print("=" * 80)
    
    # 从配置获取输入输出文件路径
    input_file = config.get('static_input_file')
    output_file = config.get('static_output_file')
    
    if not input_file:
        print("❌ 错误: 静态数据处理模式需要在配置文件中指定 static_input_file")
        print("请在配置文件中添加 static_input_file 和 static_output_file 配置项")
        sys.exit(1)
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"❌ 错误: 输入文件不存在: {input_file}")
        sys.exit(1)
    
    print(f"📂 输入文件: {input_file}")
    print(f"📁 输出文件: {output_file}")
    
    # 根据配置决定执行步骤 - 优先级：命令行参数 > 静态特定配置 > 默认值
    # 检查是否有来自命令行的明确参数（只有在显式设置时才使用）
    cmd_validation_only = getattr(args, 'dynamic_validation_only', False) if args else False
    cmd_processing_only = getattr(args, 'dynamic_processing_only', False) if args else False
    
    # 决定最终的执行模式
    if cmd_validation_only:
        # 命令行明确指定只验证
        static_validation_only = True
        static_processing_only = False
    elif cmd_processing_only:
        # 命令行明确指定只处理
        static_validation_only = False
        static_processing_only = True
    else:
        # 使用配置文件的设置（静态特定 > 默认）
        static_validation_only = config.get('static_validation_only', True)
        static_processing_only = config.get('static_processing_only', False)
    
    try:
        # 数据验证步骤
        if not static_processing_only:
            print("\n🔍 开始静态数据验证...")
            validator = StaticDataValidator(config)
            validation_results = validator.validate_static_data()
            
            # 导出验证报告
            validator.export_validation_report()
            
            # 如果只进行验证，则结束
            if static_validation_only:
                print("\n✅ 静态数据验证完成！")
                return
        
        # 数据处理步骤
        if not static_validation_only:
            print("\n🔄 开始静态数据标准化处理...")
            processor = StaticDataProcessor()
            result_df = processor.process_data(input_file, output_file)
            
            # 显示处理结果
            print("\n✅ 静态数据处理完成！")
            print(f"📊 处理的数据形状: {result_df.shape}")
            print(f"📁 输出文件已保存: {output_file}")
            
            # 显示数据预览
            print("\n📋 转换后的数据预览:")
            print(result_df.head())
        
    except Exception as e:
        print(f"❌ 静态数据处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def print_help():
    """打印帮助信息"""
    help_text = """
CAR-T治疗临床数据处理系统 - 帮助信息
==================================================

这个系统支持两种处理模式：

1. 动态数据处理模式（默认）:
   处理时间序列的动态患者数据，包括验证和清理功能。
   
   使用示例:
   # 完整处理流程
   python data_processed.py
   
   # 只进行数据验证
   python data_processed.py --validation-only
   
   # 只进行数据处理
   python data_processed.py --processing-only
   
   # 使用配置文件
   python data_processed.py --config config.yaml

2. 静态数据处理模式:
   处理患者的基础信息数据，进行标准化编码转换。
   
   使用示例:
   python data_processed.py --mode static --input patients.csv --output processed.csv

常用选项:
  --help                显示帮助信息
  --create-sample-config  创建示例配置文件
  --print-config        显示当前配置
  --mode {dynamic,static}  选择处理模式
  --input INPUT_FILE    输入文件路径（静态模式必需）
  --output OUTPUT_FILE  输出文件路径（静态模式可选）

更多选项请运行: python data_processed.py --help
"""
    print(help_text)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
