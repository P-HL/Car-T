"""
变量监控功能使用示例

本示例展示如何使用 VariableMonitor 类来监控特定变量在数据提取过程中的空数据情况。
"""

# 导入必要的库和函数
from a import VariableMonitor, extract_baseline_features
import pandas as pd

# ==============================================================
# 示例 1: 基本用法 - 监控单个变量（如CBC004）
# ==============================================================
def example_1_basic_usage():
    """
    最基本的用法：监控CBC004变量
    """
    print("\n" + "="*60)
    print("示例 1: 基本用法 - 监控CBC004")
    print("="*60)
    
    # 1. 创建监控器，指定要监控的变量
    monitor = VariableMonitor(
        variables_to_monitor=['CBC004'],  # 监控CBC004
        time_window=(-15, 0)               # 监控时间窗口 [-15, 0]
    )
    
    # 2. 假设你的数据
    patient_ids = ['P001', 'P002', 'P003']  # 替换为实际的患者ID列表
    dynamic_dir = '../datasetcart/processed'  # 替换为实际的动态数据文件夹路径
    
    # 3. 调用extract_baseline_features，传入monitor参数
    df_features = extract_baseline_features(
        patient_ids=patient_ids,
        dynamic_dir=dynamic_dir,
        time_col='Day',
        cutoff_day=0,
        monitor=monitor  # 传入监控器
    )
    
    # 4. 获取监控结果
    # 方式1: 获取空数据患者ID集合
    empty_patients = monitor.get_empty_patient_ids('CBC004')
    print(f"\nCBC004为空的患者ID: {empty_patients}")
    
    # 方式2: 打印摘要报告
    monitor.print_summary()
    
    # 方式3: 保存详细报告到文件
    monitor.save_report('monitor_report_cbc004.json')
    
    return df_features, monitor


# ==============================================================
# 示例 2: 监控多个变量
# ==============================================================
def example_2_multiple_variables():
    """
    监控多个变量的示例
    """
    print("\n" + "="*60)
    print("示例 2: 监控多个变量")
    print("="*60)
    
    # 监控多个感兴趣的变量
    monitor = VariableMonitor(
        variables_to_monitor=['CBC004', 'CBC001', 'CBC002', 'LDH', 'CRP'],
        time_window=(-15, 0)
    )
    
    # 你的实际数据
    patient_ids = ['P001', 'P002', 'P003']  # 替换为实际的患者ID列表
    dynamic_dir = '../datasetcart/processed'
    
    # 提取特征
    df_features = extract_baseline_features(
        patient_ids=patient_ids,
        dynamic_dir=dynamic_dir,
        monitor=monitor
    )
    
    # 获取所有变量的监控结果
    all_empty_patients = monitor.get_empty_patient_ids()
    
    print("\n所有变量的空数据统计:")
    for var_name, patient_set in all_empty_patients.items():
        print(f"  {var_name}: {len(patient_set)} 个患者")
        if patient_set:
            print(f"    患者ID: {sorted(list(patient_set))[:5]}")  # 显示前5个
    
    # 保存报告
    monitor.save_report('monitor_report_multiple.json')
    
    return df_features, monitor


# ==============================================================
# 示例 3: 不使用监控（向后兼容）
# ==============================================================
def example_3_without_monitoring():
    """
    如果不需要监控，可以像之前一样使用，完全向后兼容
    """
    print("\n" + "="*60)
    print("示例 3: 不使用监控功能")
    print("="*60)
    
    patient_ids = ['P001', 'P002', 'P003']
    dynamic_dir = '../datasetcart/processed'
    
    # 不传入monitor参数，功能完全正常
    df_features = extract_baseline_features(
        patient_ids=patient_ids,
        dynamic_dir=dynamic_dir
    )
    
    print("正常提取特征，不进行监控")
    print(f"提取的特征数量: {len(df_features.columns)}")
    
    return df_features


# ==============================================================
# 示例 4: 高级用法 - 分析监控结果
# ==============================================================
def example_4_analyze_results():
    """
    深入分析监控结果的示例
    """
    print("\n" + "="*60)
    print("示例 4: 高级分析 - 检查空数据原因")
    print("="*60)
    
    monitor = VariableMonitor(
        variables_to_monitor=['CBC004'],
        time_window=(-15, 0)
    )
    
    patient_ids = ['P001', 'P002', 'P003']
    dynamic_dir = '../datasetcart/processed'
    
    df_features = extract_baseline_features(
        patient_ids=patient_ids,
        dynamic_dir=dynamic_dir,
        monitor=monitor
    )
    
    # 获取详细信息
    detailed_info = monitor.detailed_info
    
    print("\nCBC004空数据的详细分析:")
    if 'CBC004' in detailed_info and detailed_info['CBC004']:
        # 按原因分组
        reasons = {}
        for pid, info in detailed_info['CBC004'].items():
            reason = info['reason']
            if reason not in reasons:
                reasons[reason] = []
            reasons[reason].append(pid)
        
        print("\n按原因分类:")
        for reason, pids in reasons.items():
            print(f"\n  原因: {reason}")
            print(f"  患者数: {len(pids)}")
            print(f"  患者ID: {pids[:5]}")  # 显示前5个
    
    # 保存详细报告
    monitor.save_report('monitor_report_detailed.json', include_details=True)
    
    return df_features, monitor


# ==============================================================
# 示例 5: 自定义时间窗口
# ==============================================================
def example_5_custom_time_window():
    """
    使用自定义时间窗口的示例
    """
    print("\n" + "="*60)
    print("示例 5: 自定义时间窗口 [-30, -1]")
    print("="*60)
    
    # 监控更长的时间窗口
    monitor = VariableMonitor(
        variables_to_monitor=['CBC004'],
        time_window=(-30, -1)  # 监控 Day -30 到 Day -1
    )
    
    patient_ids = ['P001', 'P002', 'P003']
    dynamic_dir = '../datasetcart/processed'
    
    df_features = extract_baseline_features(
        patient_ids=patient_ids,
        dynamic_dir=dynamic_dir,
        cutoff_day=-1,  # 对应time_window的上界
        monitor=monitor
    )
    
    monitor.print_summary()
    
    return df_features, monitor


# ==============================================================
# 主函数 - 运行所有示例
# ==============================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("变量监控功能示例程序")
    print("="*80)
    
    # 运行示例（根据需要选择）
    
    # 示例1: 基本用法
    # df1, monitor1 = example_1_basic_usage()
    
    # 示例2: 监控多个变量
    # df2, monitor2 = example_2_multiple_variables()
    
    # 示例3: 不使用监控
    # df3 = example_3_without_monitoring()
    
    # 示例4: 分析结果
    # df4, monitor4 = example_4_analyze_results()
    
    # 示例5: 自定义时间窗口
    # df5, monitor5 = example_5_custom_time_window()
    
    print("\n提示: 取消注释上述示例代码以运行相应的示例")
    print("\n" + "="*80)


# ==============================================================
# 快速参考
# ==============================================================
"""
快速参考指南：

1. 创建监控器:
   monitor = VariableMonitor(
       variables_to_monitor=['CBC004', 'CBC001'],
       time_window=(-15, 0)
   )

2. 在数据提取时使用:
   df = extract_baseline_features(
       patient_ids=patient_ids,
       dynamic_dir=dynamic_dir,
       monitor=monitor  # 添加这个参数
   )

3. 获取结果:
   # 获取单个变量的空患者ID
   empty_ids = monitor.get_empty_patient_ids('CBC004')
   
   # 获取所有变量的空患者ID
   all_empty = monitor.get_empty_patient_ids()
   
   # 打印摘要
   monitor.print_summary()
   
   # 保存报告
   monitor.save_report('report.json')

4. 查看详细信息:
   # 获取详细的空数据原因
   details = monitor.detailed_info['CBC004']
   
   # 每个患者的详细信息包括:
   # - reason: 为空的原因
   # - time_range: 数据的时间范围（如果有）
   # - timestamp: 记录时间

5. 空数据的可能原因:
   - 'patient_file_not_found': 患者文件不存在
   - 'time_column_missing': 时间列不存在
   - 'no_data_in_time_window': 时间窗口内没有数据
   - 'variable_not_in_file': 变量在文件中不存在
   - 'value_is_nan': 值为NaN
   - 'processing_error: ...': 处理过程中出错
"""
