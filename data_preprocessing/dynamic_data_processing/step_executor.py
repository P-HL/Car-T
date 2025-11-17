"""
步骤执行器模块
管理数据验证和处理步骤的执行
"""

import sys
import os

# 添加父目录到路径以便导入utils模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config_manager import ConfigManager
from .validator import DynamicDataValidator
from .processor import DynamicDataProcessor


class StepExecutor:
    """
    步骤执行器
    管理数据验证和处理步骤的执行
    """
    
    def __init__(self, config: ConfigManager):
        """
        初始化步骤执行器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.validation_results = None
        self.processing_results = None
    
    def validate_step_configuration(self):
        """验证步骤配置的有效性"""
        validation_only = self.config.get('dynamic_validation_only')
        processing_only = self.config.get('dynamic_processing_only')
        
        # 如果两者都未指定，默认行为：只进行验证
        if not validation_only and not processing_only:
            self.config.set('dynamic_validation_only', True)
    
    def print_execution_plan(self):
        """打印执行计划"""
        validation_only = self.config.get('dynamic_validation_only')
        processing_only = self.config.get('dynamic_processing_only')
        skip_interactive = self.config.get('skip_interactive')
        
        print("\n📋 执行计划:")
        print("-" * 50)
        
        # 根据配置显示执行步骤
        if validation_only:
            print("✅ 数据验证步骤: 启用")
        else:
            print("❌ 数据验证步骤: 禁用")
            
        if processing_only:
            print("✅ 数据处理步骤: 启用")
        else:
            print("❌ 数据处理步骤: 禁用")
        
        if skip_interactive:
            print("⚙️  交互模式: 禁用（使用配置值）")
        else:
            print("⚙️  交互模式: 启用")
        
        print("-" * 50)
    
    def execute_validation_step(self) -> bool:
        """
        执行数据验证步骤
        
        Returns:
            bool: 验证是否成功
        """
        validation_only = self.config.get('dynamic_validation_only')
        
        # 如果验证步骤未启用，则跳过
        if not validation_only:
            print("⏭️  跳过数据验证步骤（未启用）")
            return True
        
        print("\n🔍 执行数据验证步骤")
        print("=" * 60)
        
        validator = DynamicDataValidator(self.config)
        print(f"预期变量类别总数: {validator.expected_column_count}")
        print("变量类别分布:")
        
        variable_categories = self.config.get('variable_categories')
        for category, count in variable_categories.items():
            if category == 'VCN':
                print(f"- {category}: {count}个变量 ({category}001)")
            else:
                print(f"- {category}: {count}个变量 ({category}001-{category}{str(count).zfill(3)})")
        
        # 执行验证
        self.validation_results = validator.validate_all_files()
        validator.export_validation_report()
        
        # 检查验证结果
        has_valid_files = self.validation_results['valid_files'] > 0
        
        if has_valid_files:
            print(f"✅ 验证完成：发现 {self.validation_results['valid_files']} 个有效文件")
        else:
            print("❌ 验证失败：没有发现有效文件")
        
        return has_valid_files
    
    def execute_processing_step(self, validation_success: bool = True) -> bool:
        """
        执行数据处理步骤
        
        Args:
            validation_success: 验证步骤是否成功
            
        Returns:
            bool: 处理是否成功
        """
        processing_only = self.config.get('dynamic_processing_only')
        validation_only = self.config.get('dynamic_validation_only')
        
        # 如果处理步骤未启用，则跳过
        if not processing_only:
            print("⏭️  跳过数据处理步骤（未启用）")
            return True
        
        # 如果验证步骤启用且失败，则跳过处理
        if validation_only and not validation_success:
            print("⏭️  跳过数据处理步骤（验证步骤失败）")
            return False
        
        print("\n🔧 执行数据处理步骤")
        print("=" * 60)
        
        # 显示列删除配置状态
        enable_column_deletion = self.config.get('enable_column_deletion', False)
        if enable_column_deletion:
            print("✅ 列删除功能已启用")
        else:
            print("✅ 列删除功能已禁用")
        
        # 创建处理器并执行处理
        processor = DynamicDataProcessor(self.config)
        self.processing_results = processor.process_all_files(
            verbose=self.config.get('verbose')
        )
        
        # 导出处理报告
        processor.export_processing_report()
        
        # 检查处理结果
        success = self.processing_results['successful_files'] > 0
        
        if success:
            print(f"✅ 处理完成：成功处理 {self.processing_results['successful_files']} 个文件")
            print(f"📁 处理后的文件位于: {processor.output_dir}")
        else:
            print("❌ 处理失败：没有成功处理任何文件")
        
        return success
    
    def execute_all_steps(self):
        """执行所有启用的步骤"""
        self.validate_step_configuration()
        self.print_execution_plan()
        
        # 执行验证步骤
        validation_success = self.execute_validation_step()
        
        # 执行处理步骤
        processing_success = self.execute_processing_step(validation_success)
        
        # 打印最终结果
        self._print_final_results(validation_success, processing_success)
    
    def _print_final_results(self, validation_success: bool, processing_success: bool):
        """打印最终执行结果"""
        print("\n" + "=" * 80)
        print("执行结果总结")
        print("=" * 80)
        
        validation_enabled = self.config.get('dynamic_validation_only')
        processing_enabled = self.config.get('dynamic_processing_only')
        
        # 根据启用的步骤显示结果
        if validation_enabled:
            if validation_success:
                print("✅ 数据验证步骤: 成功完成")
                if self.validation_results:
                    print(f"   - 处理文件数: {self.validation_results['processed_files']}")
                    print(f"   - 有效文件数: {self.validation_results['valid_files']}")
            else:
                print("❌ 数据验证步骤: 执行失败")
        
        if processing_enabled:
            if processing_success:
                print("✅ 数据处理步骤: 成功完成")
                if self.processing_results:
                    print(f"   - 处理文件数: {self.processing_results['processed_files']}")
                    print(f"   - 成功文件数: {self.processing_results['successful_files']}")
            else:
                print("❌ 数据处理步骤: 执行失败")
        
        # 计算总体成功状态
        overall_success = True
        if validation_enabled:
            overall_success = overall_success and validation_success
        if processing_enabled:
            overall_success = overall_success and processing_success
        
        if overall_success:
            print("\n🎉 所有步骤执行完成！")
        else:
            print("\n❌ 部分步骤执行失败，请检查报告文件了解详情")
        
        print("=" * 80)
