'''
✅ 阶段1：识别硬编码值
已识别并替换的硬编码值：

文件路径: 输入目录、输出目录、静态数据路径
数据验证参数: 预期文件数量(500)、预期行数(46)、时间范围(-15到30)
列删除配置: CBC、Biochemistry、Coagulation列的删除列表
处理参数: 进度显示间隔(50)、是否显示详细信息等
输出文件路径: 验证报告和处理报告的文件名
✅ 阶段2：实现动态配置系统
命令行参数解析: 使用argparse库，支持所有配置选项
YAML配置文件: 支持完整的YAML配置文件加载
环境变量支持: 支持CART_*前缀的环境变量
配置优先级: 命令行参数 > 配置文件 > 环境变量 > 默认值
✅ 阶段3：替换硬编码值
所有硬编码值都通过config.get()方法动态获取
保持向后兼容性，原有功能完全不变
类构造函数现在接受ConfigManager实例
✅ 阶段4：提供合理默认值
所有配置选项都有合理的默认值
应用程序可以无配置开箱即用
每个配置选项都有清晰的文档说明
✅ 阶段5：文档和使用示例
创建了完整的README.md文档
包含多种使用场景的命令行示例
列出了所有支持的环境变量
提供了YAML配置文件示例
'''

# 测试新的配置系统是否工作正常
python data_processed_dynamic.py --help

# 测试打印配置功能
python data_processed_dynamic.py --print-config

# 测试使用配置文件
python data_processed_dynamic.py --config config_sample.yaml --print-config

# 测试命令行参数覆盖配置
python data_processed_dynamic.py --config config_sample.yaml --expected-file-count 600 --remove-optional-columns --print-config

# 测试环境变量
CART_EXPECTED_FILE_COUNT=700 CART_VERBOSE=false python data_processed_dynamic.py --print-config

# 测试配置优先级（命令行参数应该覆盖环境变量）
CART_EXPECTED_FILE_COUNT=700 CART_VERBOSE=false python data_processed_dynamic.py --expected-file-count 800 --no-verbose --print-config


#! 配置管理
# 创建示例配置文件
python data_processed_dynamic.py --create-sample-config

# 查看当前配置
python data_processed_dynamic.py --print-config

# 使用配置文件
python data_processed_dynamic.py --config config.yaml

#! 命令行参数示例
# 基本使用
python data_processed_dynamic.py --input-dir /path/to/input --output-dir /path/to/output

# 删除可选列
python data_processed_dynamic.py --remove-optional-columns

# 自定义参数
python data_processed_dynamic.py --expected-file-count 600 --progress-interval 100

#! 环境变量支持
export CART_INPUT_DIR="/path/to/input"
export CART_OUTPUT_DIR="/path/to/output"
export CART_REMOVE_OPTIONAL="true"
python data_processed_dynamic.py

'''
✅ 测试确认配置优先级按预期工作：

命令行参数成功覆盖环境变量
环境变量成功覆盖默认值
配置文件可以批量设置多个选项
🔧 错误处理
配置验证：检查路径存在性、数值参数有效性
类型转换：自动处理字符串到数值/布尔值的转换
错误提示：提供清晰的错误信息和使用指导
'''


python data_processed.py --mode static --input /home/phl/PHL/pytorch-forecasting/datasetcart/encoded.csv --output /home/phl/PHL/pytorch-forecasting/datasetcart/encoded_standardized.csv

python data_processed.py --config config.yaml