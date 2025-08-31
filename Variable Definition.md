# 变量定义文档
## 一、静态变量
Age
Sex
Disease
BM disease burden
Bone marrow cellularity
extramedullary mass
extranodal involvement
Ann Arbor stage
Number of prior therapy lines
Prior hematopoietic stem cell
Bridging therapy
CAR-T therapy following auto-HSCT
Costimulatory molecule
Type of construct(tandem/single target)
CAR-T cell infusion date


# 二、动态变量
CBC001
CBC002
CBC003
CBC004
CBC005
CBC006
CBC007
CBC008
CBC009
CBC010
CBC011
CBC012
CBC013
CBC014
CBC015
CBC016
CBC017
CBC018
CBC019
CBC020
CBC021
CBC022
CBC023
CBC024
Inflammatory Biomarker001
Inflammatory Biomarker002
Inflammatory Biomarker003
Inflammatory Biomarker004
Inflammatory Biomarker005
Inflammatory Biomarker006
Inflammatory Biomarker007
Inflammatory Biomarker008
Inflammatory Biomarker009
VCN001
Lymphocyte Subsets001
Lymphocyte Subsets002
Lymphocyte Subsets003
Lymphocyte Subsets004
Lymphocyte Subsets005
Lymphocyte Subsets006
Lymphocyte Subsets007
Lymphocyte Subsets008
Lymphocyte Subsets009
Lymphocyte Subsets010
Lymphocyte Subsets011
Coagulation001
Coagulation002
Coagulation003
Coagulation004
Coagulation005
Coagulation006
Coagulation007
Coagulation008
Electrolytes001
Electrolytes002
Electrolytes003
Electrolytes004
Electrolytes005
Electrolytes006
Biochemistry001
Biochemistry002
Biochemistry003
Biochemistry004
Biochemistry005
Biochemistry006
Biochemistry007
Biochemistry008
Biochemistry009
Biochemistry010
Biochemistry011
Biochemistry012
Biochemistry013
Biochemistry014
Biochemistry015
Biochemistry016
Biochemistry017
Biochemistry018
Biochemistry019
Biochemistry020
Biochemistry021
Biochemistry022
Biochemistry023
Biochemistry024
Biochemistry025
Biochemistry026
Biochemistry027
Biochemistry028
Vital Signs001
Vital Signs002
Vital Signs003
Vital Signs004
Vital Signs005



# 文档说明

### 1、项目结构


```
1. 配置文件
2. 依赖文件
3. 自定义异常
4. 数据模型
5. 配置模型
6. 日志工具
7. 数据服务接口
8. 静态数据服务
9. 动态数据服务
10. 目标变量服务
11. 主控制器
12. 入口文件
13. 测试文件示例
```
-------------


```
cart_toxicity_prediction/
├── main.py
├── config.yaml
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   └── data_service.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── static_data_service.py
│   │   ├── dynamic_data_service.py
│   │   └── target_variable_service.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── data_models.py
│   │   └── config_models.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── validators.py
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── custom_exceptions.py
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── static_eda_analyzer.py
│   │   └── dynamic_eda_analyzer.py
│   └── controllers/
│       ├── __init__.py
│       └── main_controller.py
└── tests/
    ├── __init__.py
    ├── test_services.py
    ├── test_analyzers.py
    └── test_controllers.py
```

#### 代码优势
这个重构后的代码严格遵循了您指定的所有规范：

Python 3.10+: 使用了新的类型注解语法  
命名规范: 严格遵循大驼峰、蛇形命名等规则  
SOLID原则: 每个类都有单一职责，使用接口抽象
类型注解: 全覆盖包括返回类型  
Google风格文档: 所有方法都有标准文档字符串  
日志分级: 使用DEBUG/INFO/ERROR等级别  
单元测试: 提供了测试示例  
自定义异常: 使用专门的异常类
接口契约: 实现了IDataService接口  
配置分离: 通过YAML配置文件管理  
依赖管理: 明确版本的requirements.txt  
系统架构清晰，易于维护和扩展，符合企业级代码标准。



