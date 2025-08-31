# 📝 Gemini 对话记录: gemini.py

**生成时间:** 2025年08月30日 19:17:58

## 📊 文档信息

| 项目 | 值 |
|------|-----|
| 文件名 | `gemini.py` |
| AI模型 | `gemini-2.5-flash-image-preview` |
| API密钥环境变量 | `GEMINI_API_KEY` |
| 文件大小 | 45824 字符 |
| 总行数 | 1222 行 |
| 对话数量 | 11 条 |

## 📋 目录

1. [对话轮次 1: 我正在处理一家医院的临床数据，需要分析超过 500 名患者的数据样本。我想根据这些数据生成数据分布热...](#对话轮次-1)
2. [对话轮次 2: 我需要您修改代码以完成两个特定任务： 1. 导出 CSV 文件：生成并导出一个名为 data_ava...](#对话轮次-2)
3. [对话轮次 3: 我需要对数据可视化工具进行两项增强： 1. 添加百分比格式的 CSV 导出选项：创建一个名为“百分比...](#对话轮次-3)
4. [对话轮次 4: 请在代码中添加双热图功能，以生成两种互补的可视化效果： 1.覆盖率热图：显示每个数据点的覆盖率百分比...](#对话轮次-4)
5. [对话轮次 5: 输出文件夹如何指定](#对话轮次-5)
6. [对话轮次 6: INSERT_INPUT_HERE](#对话轮次-6)

## 💬 对话内容

### 对话轮次 1

#### 👤 用户

```python
我正在处理一家医院的临床数据，需要分析超过 500 名患者的数据样本。我想根据这些数据生成数据分布热图。请根据以下要求提供标准化的数据处理代码：
数据格式：
● 数据集大小：500 例患者
● 存储位置：所有数据存储在“processed”文件夹中
● 文件结构：每位患者的数据存储在单独的 CSV 文件中，文件名为“pt_1.csv”、“pt_2.csv”等。
● 数据内容：每个 CSV 文件包含 CAR-T 治疗前 15 天和治疗后 30 天（共 45 天）的体检数据
● 数据类型：所有值均为浮点数或缺失值（NA）
● CSV 结构：
● 第一行和第一列包含索引
● 第一个单元格（第 1 行，第 1 列）代表“天”
● 第一列（y 轴）：从第 -15 天到第 30 天的时间序列
● 第一行（x 轴）：不同的变量类别，包括：
    - CBC001 ～ CBC024
    - Inflammatory Biomarker001 to Inflammatory Biomarker009
    - VCN001
    - Lymphocyte Subsets001 to Lymphocyte Subsets011
    - Coagulation001 to Coagulation008
    - Electrolytes001 to Electrolytes006
    - Biochemistry001 to Biochemistry028
    - Vital Signs001 to Vital Signs006
所需输出 - 热图规范：
● X轴：时间轴，代表45天的数据分布
● 每5天显示一个刻度标记（并非所有日期）
● 范围从第-15天到第30天
● Y轴：变量类别（按类型分组）
● 所有CBC变量合并为一行
● 所有炎症生物标志物变量合并为一行
● 所有其他变量类型同样分组为单独的行
● 可视化样式：热图格式
● 黄色块：有可用数据的时间点
● 黑色块：有缺失数据的时间点
● 热图应显示数据可用性模式全部 500 名患者
代码要求
● 使用简洁、格式良好的代码，并包含清晰的变量名称
● 添加注释，解释每个主要步骤
● 确保代码模块化且易于理解
● 提供正确标记和格式的可视化输出
● 妥善处理缺失数据（NA 值）
● 高效处理全部 500 个 CSV 文件
● 按照上述说明按类别对变量进行分组
请生成 Python 代码，该代码从“processed”文件夹读取所有患者 CSV 文件，根据这些规范处理数据，并创建所述的热图可视化效果。
```

#### 🤖 AI助手

好的，我将为您提供 Python 代码，用于处理您的临床数据并生成所需的数据分布热图。该代码将读取所有患者的 CSV 文件，处理缺失值，按类别分组变量，并生成一个热图，显示所有 500 名患者的数据可用性模式。

以下是代码：

```python
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def process_patient_data(file_path):
    \"\"\"
    读取单个患者的CSV文件并返回一个DataFrame，其中包含处理后的数据。
    \"\"\"
    df = pd.read_csv(file_path, index_col=0)
    # 将'天'列作为索引
    df.index.name = 'Day'
    return df

def create_availability_heatmap(data_frames, output_path=\"data_availability_heatmap.png\"):
    \"\"\"
    创建并保存数据可用性热图。
    \"\"\"
    # 定义变量分组
    variable_groups = {
        'CBC': [f'CBC{i:03d}' for i in range(1, 25)],
        'Inflammatory Biomarker': [f'Inflammatory Biomarker{i:03d}' for i in range(1, 10)],
        'VCN': ['VCN001'],
        'Lymphocyte Subsets': [f'Lymphocyte Subsets{i:03d}' for i in range(1, 12)],
        'Coagulation': [f'Coagulation{i:03d}' for i in range(1, 9)],
        'Electrolytes': [f'Electrolytes{i:03d}' for i in range(1, 7)],
        'Biochemistry': [f'Biochemistry{i:03d}' for i in range(1, 29)],
        'Vital Signs': [f'Vital Signs{i:03d}' for i in range(1, 7)]
    }

    # 初始化一个DataFrame来存储每个变量组和每个时间点的数据可用性计数
    # 行是时间点，列是变量组
    time_points = range(-15, 31)
    availability_matrix = pd.DataFrame(0, index=time_points, columns=variable_groups.keys())

    # 遍历每个患者的数据
    for df in data_frames:
        # 遍历每个时间点
        for day in time_points:
            if day in df.index:
                # 遍历每个变量组
                for group_name, variables in variable_groups.items():
                    # 检查该时间点和该组中是否有任何可用数据
                    # 如果该组中的任何变量在指定日期有数据，则认为该组有数据
                    available_in_group = False
                    for var in variables:
                        if var in df.columns and pd.notna(df.loc[day, var]):
                            available_in_group = True
                            break
                    if available_in_group:
                        availability_matrix.loc[day, group_name] += 1

    # 将计数转换为可用性比例（0或1），表示至少一个患者在该时间点和变量组有数据
    # 如果该时间点和变量组有任何患者数据，则为1（黄色），否则为0（黑色）
    heatmap_data = (availability_matrix > 0).astype(int).T # 转置以便X轴为时间，Y轴为变量组

    # 绘制热图
    plt.figure(figsize=(18, 10))
    sns.heatmap(
        heatmap_data,
        cmap=['black', 'yellow'],  # 0为黑色（缺失），1为黄色（可用）
        cbar=False,               # 不显示颜色条
        linewidths=0.5,           # 网格线宽度
        linecolor='gray'          # 网格线颜色
    )

    # 设置X轴刻度
    x_tick_labels = [str(day) if day % 5 == 0 else '' for day in time_points]
    plt.xticks(np.arange(len(time_points)) + 0.5, x_tick_labels, rotation=45, ha='right')
    plt.xlabel('Days (from -15 to 30)')
    plt.yticks(rotation=0)
    plt.ylabel('Variable Categories')
    plt.title('Data Availability Heatmap Across 500 Patients')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.show()

if __name__ == \"__main__\":
    processed_folder = \"processed\"
    num_patients = 500
    all_patient_data = []

    # 确保'processed'文件夹存在
    if not os.path.exists(processed_folder):
        print(f\"Error: The folder '{processed_folder}' does not exist.\")
        print(\"Please create the folder and place the patient CSV files inside.\")
        exit()

    # 读取所有患者的数据
    print(f\"Reading data for {num_patients} patients from '{processed_folder}'...\")
    for i in range(1, num_patients + 1):
        file_name = f\"pt_{i}.csv\"
        file_path = os.path.join(processed_folder, file_name)
        if os.path.exists(file_path):
            df = process_patient_data(file_path)
            all_patient_data.append(df)
        else:
            print(f\"Warning: File '{file_path}' not found. Skipping patient {i}.\")

    if not all_patient_data:
        print(\"No patient data found. Exiting.\")
    else:
        print(\"All patient data loaded. Generating heatmap...\")
        # 创建并显示热图
        create_availability_heatmap(all_patient_data)
        print(\"Heatmap generated and saved as 'data_availability_heatmap.png'.\")
```

### 如何使用此代码：

1.  **准备数据：**
    *   在您的工作目录中创建一个名为 `processed` 的文件夹。
    *   将所有患者的 CSV 文件（例如 `pt_1.csv`, `pt_2.csv` 等）放入 `processed` 文件夹中。请确保文件命名符合代码中 `pt_{i}.csv` 的格式。
    *   确保您的 CSV 文件结构与您描述的一致（第一列为天数，第一行为变量名称）。

2.  **运行代码：**
    *   将上述 Python 代码保存为一个 `.py` 文件（例如 `heatmap_generator.py`）。
    *   在终端或命令提示符中，导航到保存文件的目录，然后运行：
        ```bash
        python heatmap_generator.py
        ```

3.  **查看结果：**
    *   代码运行完成后，将在与 `.py` 文件相同的目录下生成一个名为 `data_availability_heatmap.png` 的热图文件。
    *   热图将显示所有 500 名患者在每个时间点和每个变量类别下的数据可用性。黄色表示在该时间点和变量组至少有一名患者有可用数据，黑色表示该时间点和变量组所有患者都缺失数据。

### 代码解释：

*   **`process_patient_data(file_path)`:**
    *   此函数负责读取单个患者的 CSV 文件。
    *   它使用 `pd.read_csv` 读取文件，并将第一列（天数）设置为 DataFrame 的索引。

*   **`create_availability_heatmap(data_frames, output_path)`:**
    *   这是生成热图的核心函数。
    *   **`variable_groups`:** 一个字典，定义了您要求的变量分组。键是组名（例如 'CBC'），值是该组中所有变量的列表。
    *   **`availability_matrix`:** 初始化一个 DataFrame，用于存储在每个时间点和每个变量组中至少有多少名患者拥有数据。行是天数，列是变量组。
    *   **数据遍历和可用性计算：**
        *   代码遍历每个患者的 DataFrame。
        *   对于每个患者和每个时间点（从 -15 到 30），它会检查每个变量组。
        *   如果某个变量组中**任何**一个变量在该特定日期有非缺失值，则认为该组在该日期有数据，并将 `availability_matrix` 中相应单元格的计数加 1。
    *   **`heatmap_data`:** 将 `availability_matrix` 转换为一个布尔 DataFrame，其中如果计数大于 0，则为 1（表示有数据），否则为 0（表示无数据）。然后将其转置，使行成为变量组，列成为时间点，以符合热图的X/Y轴要求。
    *   **热图绘制：**
        *   使用 `matplotlib.pyplot` 和 `seaborn` 库来创建热图。
        *   `cmap=['black', 'yellow']` 设置颜色映射，其中 0 映射到黑色（缺失），1 映射到黄色（可用）。
        *   `xticks` 和 `yticks` 设置轴标签，特别是X轴每 5 天显示一个刻度。
        *   `plt.savefig` 将生成的热图保存为 PNG 文件。

*   **`if __name__ == \"__main__\":` (主执行块):**
    *   设置 `processed_folder` 和 `num_patients`。
    *   检查 `processed` 文件夹是否存在。
    *   循环读取所有患者的 CSV 文件，并调用 `process_patient_data` 函数。
    *   将所有患者的数据存储在 `all_patient_data` 列表中。
    *   最后，调用 `create_availability_heatmap` 函数来生成并保存热图。

这个代码应该能够满足您的所有要求，提供清晰的可视化效果，并高效处理大量数据。

---

### 对话轮次 2

#### 👤 用户

我需要您修改代码以完成两个特定任务：
1. 导出 CSV 文件：生成并导出一个名为 data_availability_fraction.csv 的文件，其中包含数据可用性覆盖率（范围从 0 到 1），其组织方式如下：
● 行：不同类别/类型
● 列：日期
● 值：覆盖率分数（0 到 1 之间的小数值）
2. 更新热图可视化：将当前热图从离散颜色映射转换为表示百分比的连续色标：
● 将离散色标更改为平滑渐变
● 将值显示为百分比（0% 到 100%）
● 确保色标在整个值范围内平滑过渡
● 热图应以基于百分比的连续色标直观地表示数据可用性
请在同一代码修改中同时实现 CSV 导出功能和连续百分比热图可视化。

#### 🤖 AI助手

好的，我将修改代码以实现这两个任务：导出包含数据可用性覆盖率的 CSV 文件，并将热图的可视化更新为表示百分比的连续色标。

以下是修改后的 Python 代码：

```python
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def process_patient_data(file_path):
    \"\"\"
    读取单个患者的CSV文件并返回一个DataFrame，其中包含处理后的数据。
    \"\"\"
    df = pd.read_csv(file_path, index_col=0)
    # 将'天'列作为索引
    df.index.name = 'Day'
    return df

def analyze_and_visualize_availability(data_frames, num_patients, output_csv_path=\"data_availability_fraction.csv\", output_heatmap_path=\"data_availability_heatmap_percentage.png\"):
    \"\"\"
    分析数据可用性，导出CSV文件，并创建连续百分比热图。
    \"\"\"
    # 定义变量分组
    variable_groups = {
        'CBC': [f'CBC{i:03d}' for i in range(1, 25)],
        'Inflammatory Biomarker': [f'Inflammatory Biomarker{i:03d}' for i in range(1, 10)],
        'VCN': ['VCN001'],
        'Lymphocyte Subsets': [f'Lymphocyte Subsets{i:03d}' for i in range(1, 12)],
        'Coagulation': [f'Coagulation{i:03d}' for i in range(1, 9)],
        'Electrolytes': [f'Electrolytes{i:03d}' for i in range(1, 7)],
        'Biochemistry': [f'Biochemistry{i:03d}' for i in range(1, 29)],
        'Vital Signs': [f'Vital Signs{i:03d}' for i in range(1, 7)]
    }

    # 初始化一个DataFrame来存储每个变量组和每个时间点的数据可用性计数
    # 行是时间点，列是变量组
    time_points = range(-15, 31)
    availability_counts_matrix = pd.DataFrame(0, index=time_points, columns=variable_groups.keys())

    # 遍历每个患者的数据
    for df in data_frames:
        # 遍历每个时间点
        for day in time_points:
            if day in df.index:
                # 遍历每个变量组
                for group_name, variables in variable_groups.items():
                    # 检查该时间点和该组中是否有任何可用数据
                    # 如果该组中的任何变量在指定日期有数据，则认为该组在该日期有数据
                    available_in_group = False
                    for var in variables:
                        if var in df.columns and pd.notna(df.loc[day, var]):
                            available_in_group = True
                            break
                    if available_in_group:
                        availability_counts_matrix.loc[day, group_name] += 1

    # 计算可用性覆盖率（分数从 0 到 1）
    # availability_counts_matrix 记录了在该时间点和变量组拥有数据的患者数量
    # num_patients 是总患者数
    data_availability_fraction = (availability_counts_matrix / num_patients).T # 转置以便行是类别，列是日期

    # 1. 导出 CSV 文件
    data_availability_fraction.to_csv(output_csv_path)
    print(f\"Data availability fraction exported to '{output_csv_path}'\")

    # 2. 更新热图可视化为连续百分比色标
    plt.figure(figsize=(18, 10))
    sns.heatmap(
        data_availability_fraction * 100, # 将分数转换为百分比
        cmap='viridis',                  # 使用连续色标，例如 'viridis', 'plasma', 'magma', 'cividis'
        cbar=True,                       # 显示颜色条
        linewidths=0.5,                  # 网格线宽度
        linecolor='gray',                # 网格线颜色
        fmt=\".0f\",                       # 格式化注释，显示整数百分比
        annot=False,                     # 不在每个单元格显示数值，颜色条已足够
        vmin=0, vmax=100                 # 确保色标范围从0到100
    )

    # 设置颜色条标签
    cbar = plt.gca().collections[0].colorbar
    cbar.set_label('Data Availability (%)', rotation=270, labelpad=20)

    # 设置X轴刻度
    x_tick_labels = [str(day) if day % 5 == 0 else '' for day in time_points]
    plt.xticks(np.arange(len(time_points)) + 0.5, x_tick_labels, rotation=45, ha='right')
    plt.xlabel('Days (from -15 to 30)')
    plt.yticks(rotation=0)
    plt.ylabel('Variable Categories')
    plt.title('Data Availability Heatmap Across Patients (Percentage)')
    plt.tight_layout()
    plt.savefig(output_heatmap_path, dpi=300)
    plt.show()

if __name__ == \"__main__\":
    processed_folder = \"processed\"
    num_patients = 500
    all_patient_data = []

    # 确保'processed'文件夹存在
    if not os.path.exists(processed_folder):
        print(f\"Error: The folder '{processed_folder}' does not exist.\")
        print(\"Please create the folder and place the patient CSV files inside.\")
        exit()

    # 读取所有患者的数据
    print(f\"Reading data for {num_patients} patients from '{processed_folder}'...\")
    for i in range(1, num_patients + 1):
        file_name = f\"pt_{i}.csv\"
        file_path = os.path.join(processed_folder, file_name)
        if os.path.exists(file_path):
            df = process_patient_data(file_path)
            all_patient_data.append(df)
        else:
            print(f\"Warning: File '{file_path}' not found. Skipping patient {i}.\")

    if not all_patient_data:
        print(\"No patient data found. Exiting.\")
    else:
        print(\"All patient data loaded. Analyzing availability and generating output...\")
        # 分析可用性、导出CSV并创建热图
        analyze_and_visualize_availability(all_patient_data, num_patients)
        print(\"Analysis complete. Check 'data_availability_fraction.csv' and 'data_availability_heatmap_percentage.png'.\")

```

### 修改说明：

1.  **数据可用性覆盖率计算：**
    *   在 `analyze_and_visualize_availability` 函数中，`availability_counts_matrix` 仍然用于统计在每个时间点和每个变量组有多少名患者拥有数据。
    *   新增一行：`data_availability_fraction = (availability_counts_matrix / num_patients).T`。这将每个单元格的计数除以总患者数 `num_patients`，从而得到一个 0 到 1 之间的分数，表示该时间点和变量组的数据可用性覆盖率。 `.T` 将其转置，以确保行是类别，列是日期。

2.  **导出 CSV 文件 (`data_availability_fraction.csv`)：**
    *   使用 `data_availability_fraction.to_csv(output_csv_path)` 将计算出的覆盖率数据导出到 CSV 文件中。
    *   CSV 文件的结构将符合您的要求：行是变量类别，列是日期，值是 0 到 1 之间的覆盖率分数。

3.  **更新热图可视化：**
    *   **连续色标：** `cmap='viridis'` 被用于代替之前的离散色标。`viridis` 是 `matplotlib` 和 `seaborn` 中一个常用的、感知均匀的连续色标。您也可以尝试其他选项，如 `'plasma'`, `'magma'`, `'cividis'` 等。
    *   **显示百分比：**
        *   `sns.heatmap(data_availability_fraction * 100, ...)`：在绘制热图时，我们将可用性分数乘以 100，使其显示为百分比。
        *   `cbar=True`：确保颜色条可见，以便用户可以理解颜色的含义。
        *   `vmin=0, vmax=100`：明确设置颜色映射的范围从 0% 到 100%，确保平滑过渡。
        *   `cbar.set_label('Data Availability (%)', rotation=270, labelpad=20)`：为颜色条添加一个清晰的标签，指示它表示百分比。
        *   `annot=False`：为了保持热图的整洁，在连续色标的情况下，通常不需要在每个单元格内显示数值，颜色条已经提供了足够的信息。

4.  **函数名称更改：** 将 `create_availability_heatmap` 函数重命名为 `analyze_and_visualize_availability`，以更好地反映它现在执行多项任务（分析、导出和可视化）。

### 运行说明：

1.  确保您的 `processed` 文件夹和 CSV 文件已准备好，与之前的说明相同。
2.  保存修改后的 Python 代码。
3.  运行脚本。

您将得到两个输出：
*   一个名为 `data_availability_fraction.csv` 的 CSV 文件，其中包含按类别和日期组织的数据可用性覆盖率分数。
*   一个名为 `data_availability_heatmap_percentage.png` 的热图图像，它使用连续色标可视化了数据可用性百分比。

---

### 对话轮次 3

#### 👤 用户

我需要对数据可视化工具进行两项增强：
1. 添加百分比格式的 CSV 导出选项：创建一个名为“百分比 CSV”的附加导出选项，将缺失值百分比导出为整数 (0-100)，而不是小数 (0-1)。例如，25% 的缺失率应导出为“25”，而不是“0.25”。
2. 改进热图缺失值的视觉对比度：增强热图的配色方案，使缺失值和非缺失值之间的差异更加直观。当前热图不同缺失值百分比之间的颜色对比度不足，导致难以区分不同缺失数据级别的区域。请：
- 增加低缺失值百分比和高缺失值百分比之间的颜色对比度
- 考虑使用更鲜明的调色板（例如，白色表示 0% 缺失，深蓝色表示 100% 缺失）
- 确保缺失值百分比之间的细微差异在热图中清晰可见

#### 🤖 AI助手

好的，我将再次修改代码以满足您的新要求：

1.  **添加百分比格式的 CSV 导出选项：** 创建一个名为 `data_missing_percentage.csv` 的新文件，导出缺失值百分比，格式为 0-100 的整数。
2.  **改进热图缺失值的视觉对比度：** 增强热图配色方案，使用更鲜明的调色板，使缺失值百分比之间的差异更加直观，例如白色表示 0% 缺失，深蓝色表示 100% 缺失。

以下是修改后的 Python 代码：

```python
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def process_patient_data(file_path):
    \"\"\"
    读取单个患者的CSV文件并返回一个DataFrame，其中包含处理后的数据。
    \"\"\"
    df = pd.read_csv(file_path, index_col=0)
    # 将'天'列作为索引
    df.index.name = 'Day'
    return df

def analyze_and_visualize_availability(data_frames, num_patients, 
                                     output_availability_fraction_csv=\"data_availability_fraction.csv\",
                                     output_missing_percentage_csv=\"data_missing_percentage.csv\",
                                     output_heatmap_path=\"data_missing_percentage_heatmap.png\"):
    \"\"\"
    分析数据可用性，导出CSV文件，并创建连续百分比热图（聚焦缺失值）。
    \"\"\"
    # 定义变量分组
    variable_groups = {
        'CBC': [f'CBC{i:03d}' for i in range(1, 25)],
        'Inflammatory Biomarker': [f'Inflammatory Biomarker{i:03d}' for i in range(1, 10)],
        'VCN': ['VCN001'],
        'Lymphocyte Subsets': [f'Lymphocyte Subsets{i:03d}' for i in range(1, 12)],
        'Coagulation': [f'Coagulation{i:03d}' for i in range(1, 9)],
        'Electrolytes': [f'Electrolytes{i:03d}' for i in range(1, 7)],
        'Biochemistry': [f'Biochemistry{i:03d}' for i in range(1, 29)],
        'Vital Signs': [f'Vital Signs{i:03d}' for i in range(1, 7)]
    }

    # 初始化一个DataFrame来存储每个变量组和每个时间点的数据可用性计数
    time_points = range(-15, 31)
    availability_counts_matrix = pd.DataFrame(0, index=time_points, columns=variable_groups.keys())

    # 遍历每个患者的数据
    for df in data_frames:
        # 遍历每个时间点
        for day in time_points:
            if day in df.index:
                # 遍历每个变量组
                for group_name, variables in variable_groups.items():
                    # 检查该时间点和该组中是否有任何可用数据
                    available_in_group = False
                    for var in variables:
                        if var in df.columns and pd.notna(df.loc[day, var]):
                            available_in_group = True
                            break
                    if available_in_group:
                        availability_counts_matrix.loc[day, group_name] += 1

    # 计算可用性覆盖率（分数从 0 到 1）
    data_availability_fraction = (availability_counts_matrix / num_patients).T 

    # 1. 导出原始数据可用性分数 CSV 文件
    data_availability_fraction.to_csv(output_availability_fraction_csv)
    print(f\"Data availability fraction exported to '{output_availability_fraction_csv}'\")

    # 计算缺失值百分比（0-100 整数）
    # 缺失值 = 1 - 可用性
    data_missing_percentage = ((1 - data_availability_fraction) * 100).astype(int)

    # 2. 导出百分比格式的 CSV 文件 (缺失值)
    data_missing_percentage.to_csv(output_missing_percentage_csv)
    print(f\"Data missing percentage (0-100) exported to '{output_missing_percentage_csv}'\")


    # 3. 改进热图缺失值的视觉对比度
    plt.figure(figsize=(18, 10))
    sns.heatmap(
        data_missing_percentage,   # 使用缺失值百分比数据
        cmap='Blues',              # 使用Blues调色板，白色到深蓝色，白色代表低缺失，深蓝色代表高缺失
        cbar=True,                 # 显示颜色条
        linewidths=0.5,            # 网格线宽度
        linecolor='gray',          # 网格线颜色
        fmt=\".0f\",                 # 格式化注释，显示整数百分比
        annot=False,               # 不在每个单元格显示数值，颜色条已足够
        vmin=0, vmax=100           # 确保色标范围从0到100
    )

    # 设置颜色条标签
    cbar = plt.gca().collections[0].colorbar
    cbar.set_label('Missing Data (%)', rotation=270, labelpad=20)

    # 设置X轴刻度
    x_tick_labels = [str(day) if day % 5 == 0 else '' for day in time_points]
    plt.xticks(np.arange(len(time_points)) + 0.5, x_tick_labels, rotation=45, ha='right')
    plt.xlabel('Days (from -15 to 30)')
    plt.yticks(rotation=0)
    plt.ylabel('Variable Categories')
    plt.title('Missing Data Percentage Heatmap Across Patients')
    plt.tight_layout()
    plt.savefig(output_heatmap_path, dpi=300)
    plt.show()

if __name__ == \"__main__\":
    processed_folder = \"processed\"
    num_patients = 500
    all_patient_data = []

    # 确保'processed'文件夹存在
    if not os.path.exists(processed_folder):
        print(f\"Error: The folder '{processed_folder}' does not exist.\")
        print(\"Please create the folder and place the patient CSV files inside.\")
        exit()

    # 读取所有患者的数据
    print(f\"Reading data for {num_patients} patients from '{processed_folder}'...\")
    for i in range(1, num_patients + 1):
        file_name = f\"pt_{i}.csv\"
        file_path = os.path.join(processed_folder, file_name)
        if os.path.exists(file_path):
            df = process_patient_data(file_path)
            all_patient_data.append(df)
        else:
            print(f\"Warning: File '{file_path}' not found. Skipping patient {i}.\")

    if not all_patient_data:
        print(\"No patient data found. Exiting.\")
    else:
        print(\"All patient data loaded. Analyzing availability and generating output...\")
        # 分析可用性、导出CSV并创建热图
        analyze_and_visualize_availability(all_patient_data, num_patients)
        print(\"Analysis complete. Check 'data_availability_fraction.csv', 'data_missing_percentage.csv', and 'data_missing_percentage_heatmap.png'.\")

```

### 修改说明：

1.  **计算缺失值百分比：**
    *   在 `analyze_and_visualize_availability` 函数中，我们首先计算了 `data_availability_fraction` (可用性分数，0-1)。
    *   然后，通过 `data_missing_percentage = ((1 - data_availability_fraction) * 100).astype(int)` 计算出缺失值百分比。这里：
        *   `1 - data_availability_fraction` 得到缺失值的比例 (0-1)。
        *   乘以 `100` 转换为百分比。
        *   `.astype(int)` 将浮点数转换为整数，符合您的要求。

2.  **导出百分比格式的 CSV 文件 (`data_missing_percentage.csv`)：**
    *   `data_missing_percentage.to_csv(output_missing_percentage_csv)` 将这个新的缺失值百分比 DataFrame 导出到 CSV 文件中。这个文件将包含 0-100 的整数值。
    *   为了区分，原来的可用性分数 CSV 仍然会导出为 `data_availability_fraction.csv`。

3.  **改进热图缺失值的视觉对比度：**
    *   **数据源切换：** 热图现在绘制的是 `data_missing_percentage`，而不是 `data_availability_fraction`。这意味着颜色现在直接表示缺失值的百分比。
    *   **调色板更改：** `cmap='Blues'`。
        *   `'Blues'` 是 `matplotlib` 和 `seaborn` 中一个非常适合表示从低到高强度值的顺序调色板。
        *   在这种调色板中，**浅色（接近白色）代表低值（0% 缺失）**，而**深色（深蓝色）代表高值（100% 缺失）**。这完美符合您“白色表示 0% 缺失，深蓝色表示 100% 缺失”的要求，并能增强低缺失和高缺失之间的视觉对比度。
    *   **颜色条标签：** `cbar.set_label('Missing Data (%)', ...)` 将颜色条的标签更新为“Missing Data (%)”，以准确反映热图的内容。
    *   **输出文件名称：** 热图保存为 `data_missing_percentage_heatmap.png` 以反映其内容。

### 运行说明：

1.  确保您的 `processed` 文件夹和 CSV 文件已准备好。
2.  保存修改后的 Python 代码。
3.  运行脚本。

您将得到三个输出文件：
*   `data_availability_fraction.csv`：包含 0 到 1 之间小数的原始数据可用性分数。
*   `data_missing_percentage.csv`：包含 0 到 100 之间整数的缺失数据百分比。
*   `data_missing_percentage_heatmap.png`：更新后的热图，使用白色到深蓝色的连续色标，以直观地表示缺失数据百分比，并增强了对比度。

---

### 对话轮次 4

#### 👤 用户

```python
请在代码中添加双热图功能，以生成两种互补的可视化效果：
1.覆盖率热图：显示每个数据点的覆盖率百分比/比率
2.缺失/缺口热图：显示每个数据点的缺失数据百分比/比率
要求：
- 两种热图均应符合学术论文发表的要求，并采用专业格式
- 确保输出格式符合学术严谨性（正确的标签、图例、配色方案等）
- 实现可配置选项以控制：
- 生成哪个版本（原版本、仅覆盖、仅缺失、覆盖缺失两者兼有）
- 输出格式（例如，用于发表的 PNG、PDF、SVG）
- 配色方案选择
- 图形大小和分辨率设置
- 是否显示为单独的图形或并排比较

目标是在保持一致、专业的可视化标准的同时，为学术出版物中的不同呈现需求提供灵活性。
```

#### 🤖 AI助手

好的，这一个更全面的更新，我将集成双热图功能，并添加详细的可配置选项，使其满足学术论文发表的要求，同时提供灵活的输出格式和可视化方式。

我们将引入一个新的函数来处理热图的生成，并将其参数化，以控制不同的可视化需求。

以下是修改后的 Python 代码：

```python
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def process_patient_data(file_path):
    \"\"\"
    读取单个患者的CSV文件并返回一个DataFrame，其中包含处理后的数据。
    \"\"\"
    df = pd.read_csv(file_path, index_col=0)
    # 将'天'列作为索引
    df.index.name = 'Day'
    return df

def generate_heatmap(data, title, cbar_label, cmap, vmin, vmax, ax, figsize_single=(12, 8), time_points=None):
    \"\"\"
    生成单个热图的通用函数。
    \"\"\"
    sns.heatmap(
        data,
        cmap=cmap,
        cbar=True,
        linewidths=0.5,
        linecolor='lightgray', # 使用更浅的网格线颜色，避免分散注意力
        fmt=\".0f\",
        annot=False,
        vmin=vmin,
        vmax=vmax,
        ax=ax,
        cbar_kws={\"label\": cbar_label, \"orientation\": \"vertical\", \"pad\": 0.03} # 调整颜色条标签和位置
    )
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Days (from -15 to 30)', fontsize=12)
    ax.set_ylabel('Variable Categories', fontsize=12)

    # 设置X轴刻度
    if time_points is not None:
        x_tick_labels = [str(day) if day % 5 == 0 else '' for day in time_points]
        ax.set_xticks(np.arange(len(time_points)) + 0.5)
        ax.set_xticklabels(x_tick_labels, rotation=45, ha='right', fontsize=10)
    ax.tick_params(axis='y', rotation=0, labelsize=10)


def analyze_and_visualize_data(data_frames, num_patients, config):
    \"\"\"
    分析数据可用性，导出CSV文件，并根据配置生成热图。
    \"\"\"
    # 定义变量分组
    variable_groups = {
        'CBC': [f'CBC{i:03d}' for i in range(1, 25)],
        'Inflammatory Biomarker': [f'Inflammatory Biomarker{i:03d}' for i in range(1, 10)],
        'VCN': ['VCN001'],
        'Lymphocyte Subsets': [f'Lymphocyte Subsets{i:03d}' for i in range(1, 12)],
        'Coagulation': [f'Coagulation{i:03d}' for i in range(1, 9)],
        'Electrolytes': [f'Electrolytes{i:03d}' for i in range(1, 7)],
        'Biochemistry': [f'Biochemistry{i:03d}' for i in range(1, 29)],
        'Vital Signs': [f'Vital Signs{i:03d}' for i in range(1, 7)]
    }

    time_points = range(-15, 31)
    availability_counts_matrix = pd.DataFrame(0, index=time_points, columns=variable_groups.keys())

    for df in data_frames:
        for day in time_points:
            if day in df.index:
                for group_name, variables in variable_groups.items():
                    available_in_group = False
                    for var in variables:
                        if var in df.columns and pd.notna(df.loc[day, var]):
                            available_in_group = True
                            break
                    if available_in_group:
                        availability_counts_matrix.loc[day, group_name] += 1

    # 计算可用性覆盖率（分数从 0 到 1）
    data_availability_fraction = (availability_counts_matrix / num_patients).T 

    # 计算缺失值百分比（0-100 整数）
    data_missing_percentage = ((1 - data_availability_fraction) * 100).astype(int)

    # 导出 CSV 文件
    if config['export_csv_availability']:
        output_availability_fraction_csv = f\"data_availability_fraction.{config['csv_export_format']}\"
        data_availability_fraction.to_csv(output_availability_fraction_csv)
        print(f\"Data availability fraction exported to '{output_availability_fraction_csv}'\")

    if config['export_csv_missing']:
        output_missing_percentage_csv = f\"data_missing_percentage.{config['csv_export_format']}\"
        data_missing_percentage.to_csv(output_missing_percentage_csv)
        print(f\"Data missing percentage (0-100) exported to '{output_missing_percentage_csv}'\")


    # 热图生成
    if config['generate_heatmap_availability'] or config['generate_heatmap_missing']:
        
        plt.style.use('seaborn-v0_8-whitegrid') # 尝试使用更专业的matplotlib样式
        
        if config['heatmap_layout'] == 'side_by_side' and config['generate_heatmap_availability'] and config['generate_heatmap_missing']:
            # 并排显示双热图
            fig, axes = plt.subplots(1, 2, figsize=config['figsize_double'], dpi=config['dpi'])
            
            # 覆盖率热图
            generate_heatmap(
                data_availability_fraction * 100,
                'Data Coverage (%)',
                'Coverage (%)',
                config['cmap_availability'],
                0, 100,
                ax=axes[0],
                time_points=time_points
            )
            
            # 缺失/缺口热图
            generate_heatmap(
                data_missing_percentage,
                'Missing Data (%)',
                'Missing (%)',
                config['cmap_missing'],
                0, 100,
                ax=axes[1],
                time_points=time_points
            )
            plt.tight_layout()
            output_file = f\"heatmap_coverage_and_missing_side_by_side.{config['output_format']}\"
            plt.savefig(output_file, format=config['output_format'])
            print(f\"Side-by-side heatmaps saved to '{output_file}'\")
            plt.show()

        else: # 单独显示或仅生成一个
            if config['generate_heatmap_availability']:
                fig, ax = plt.subplots(1, 1, figsize=config['figsize_single'], dpi=config['dpi'])
                generate_heatmap(
                    data_availability_fraction * 100,
                    'Data Coverage (%)',
                    'Coverage (%)',
                    config['cmap_availability'],
                    0, 100,
                    ax=ax,
                    time_points=time_points
                )
                plt.tight_layout()
                output_file = f\"heatmap_coverage.{config['output_format']}\"
                plt.savefig(output_file, format=config['output_format'])
                print(f\"Coverage heatmap saved to '{output_file}'\")
                plt.show()

            if config['generate_heatmap_missing']:
                fig, ax = plt.subplots(1, 1, figsize=config['figsize_single'], dpi=config['dpi'])
                generate_heatmap(
                    data_missing_percentage,
                    'Missing Data (%)',
                    'Missing (%)',
                    config['cmap_missing'],
                    0, 100,
                    ax=ax,
                    time_points=time_points
                )
                plt.tight_layout()
                output_file = f\"heatmap_missing.{config['output_format']}\"
                plt.savefig(output_file, format=config['output_format'])
                print(f\"Missing data heatmap saved to '{output_file}'\")
                plt.show()

if __name__ == \"__main__\":
    processed_folder = \"processed\"
    num_patients = 500
    all_patient_data = []

    # --- 配置选项 ---
    config = {
        # CSV 导出选项
        'export_csv_availability': True,  # 导出可用性分数 (0-1) CSV
        'export_csv_missing': True,       # 导出缺失百分比 (0-100 整数) CSV
        'csv_export_format': 'csv',       # CSV 导出格式 (例如: 'csv')

        # 热图生成选项
        'generate_heatmap_availability': True, # 生成覆盖率热图
        'generate_heatmap_missing': True,      # 生成缺失/缺口热图

        # 热图布局：'separate' (单独显示) 或 'side_by_side' (并排显示，仅当 generate_heatmap_availability 和 generate_heatmap_missing 都为 True 时有效)
        'heatmap_layout': 'side_by_side',  

        # 输出格式：'png', 'pdf', 'svg'
        'output_format': 'png',           

        # 配色方案选择
        'cmap_availability': 'viridis',    # 覆盖率热图的颜色映射 (0% 覆盖 -> 紫色, 100% 覆盖 -> 黄色)
        'cmap_missing': 'Blues',           # 缺失热图的颜色映射 (0% 缺失 -> 白色, 100% 缺失 -> 深蓝色)
                                           # 其他选择如 'RdYlGn_r' (红色-黄色-绿色 反转), 'YlOrRd' (黄-橙-红)

        # 图形大小和分辨率
        'figsize_single': (14, 8),         # 单个热图的图形大小 (宽, 高 英寸)
        'figsize_double': (24, 8),         # 并排热图的图形大小 (宽, 高 英寸)
        'dpi': 300,                        # 图像分辨率 (每英寸点数)
    }
    # ------------------

    # 确保'processed'文件夹存在
    if not os.path.exists(processed_folder):
        print(f\"Error: The folder '{processed_folder}' does not exist.\")
        print(\"Please create the folder and place the patient CSV files inside.\")
        exit()

    # 读取所有患者的数据
    print(f\"Reading data for {num_patients} patients from '{processed_folder}'...\")
    for i in range(1, num_patients + 1):
        file_name = f\"pt_{i}.csv\"
        file_path = os.path.join(processed_folder, file_name)
        if os.path.exists(file_path):
            df = process_patient_data(file_path)
            all_patient_data.append(df)
        else:
            print(f\"Warning: File '{file_path}' not found. Skipping patient {i}.\")

    if not all_patient_data:
        print(\"No patient data found. Exiting.\")
    else:
        print(\"All patient data loaded. Analyzing availability and generating output...\")
        analyze_and_visualize_data(all_patient_data, num_patients, config)
        print(\"Analysis complete based on configuration.\")
```

### 主要增强和功能：

1.  **`generate_heatmap` 通用函数：**
    *   创建了一个通用的 `generate_heatmap` 函数，它接受数据、标题、颜色条标签、颜色映射等参数，以便在生成两种热图时重用代码并保持一致性。
    *   **学术格式改进：**
        *   `plt.style.use('seaborn-v0_8-whitegrid')`：引入了 `seaborn` 的样式，通常用于学术出版物，提供更清晰的背景和网格。
        *   字体大小 (`fontsize`) 和粗细 (`fontweight`) 调整，使标题和轴标签更具可读性。
        *   颜色条标签现在垂直显示 (`orientation=\"vertical\"`)，并调整了 `pad` 以改善布局。
        *   网格线颜色改为 `lightgray`，以减少干扰。

2.  **配置字典 (`config`)：**
    *   所有可配置的选项都集中在一个 `config` 字典中，位于 `if __name__ == \"__main__\":` 块内，便于用户轻松修改。
    *   **CSV 导出选项：**
        *   `export_csv_availability`: 控制是否导出可用性分数 CSV。
        *   `export_csv_missing`: 控制是否导出缺失百分比 CSV。
        *   `csv_export_format`: CSV 文件的扩展名（默认为 'csv'）。
    *   **热图生成选项：**
        *   `generate_heatmap_availability`: 控制是否生成覆盖率热图。
        *   `generate_heatmap_missing`: 控制是否生成缺失/缺口热图。
    *   **热图布局 (`heatmap_layout`)：**
        *   `'separate'`：默认行为，如果两种热图都生成，则显示为两个独立的图形。
        *   `'side_by_side'`：如果 `generate_heatmap_availability` 和 `generate_heatmap_missing` 都为 `True`，则将两种热图并排显示在一个图形中。
    *   **输出格式 (`output_format`)：**
        *   支持 `'png'` (默认), `'pdf'`, `'svg'` 等，这些是学术出版物中常用的高质量矢量或光栅图像格式。
    *   **配色方案选择：**
        *   `cmap_availability`: 用于覆盖率热图的颜色映射。默认为 `'viridis'`，从紫色（低覆盖）到黄色（高覆盖）。
        *   `cmap_missing`: 用于缺失热图的颜色映射。默认为 `'Blues'`，从白色（低缺失）到深蓝色（高缺失）。这些选择是为了增强对比度。
    *   **图形大小和分辨率：**
        *   `figsize_single`: 单个热图的尺寸。
        *   `figsize_double`: 并排热图的尺寸，通常需要更宽。
        *   `dpi`: 输出图像的分辨率，学术论文通常要求较高的 DPI (例如 300 或 600)。

3.  **双热图逻辑：**
    *   `analyze_and_visualize_data` 函数现在包含根据 `config['heatmap_layout']` 和是否启用两种热图来决定如何绘制图形的逻辑。
    *   如果选择 `'side_by_side'` 且两种热图都启用，则使用 `plt.subplots(1, 2, ...)` 创建两个子图并进行绘制。
    *   否则，将分别创建独立的图形。

### 如何使用：

1.  **数据准备：** 确保 `processed` 文件夹存在且包含所有 `pt_*.csv` 文件。
2.  **配置：** 根据您的需求修改 `config` 字典中的值。
    *   例如，如果您只想生成 PDF 格式的缺失热图，您可以设置：
        ```python
        config = {
            'export_csv_availability': False,
            'export_csv_missing': False,
            'generate_heatmap_availability': False,
            'generate_heatmap_missing': True,
            'heatmap_layout': 'separate',
            'output_format': 'pdf',
            'cmap_missing': 'Reds', # 尝试不同的调色板
            'figsize_single': (10, 6),
            'dpi': 600,
        }
        ```
3.  **运行代码：** 运行 Python 脚本。
4.  **检查输出：** 在脚本所在的目录下，您会找到生成的 CSV 文件和热图图像文件，其名称和格式将根据您的配置。

这个增强版本提供了极大的灵活性和专业级的输出，非常适合学术出版物。

---

### 对话轮次 5

#### 👤 用户

输出文件夹如何指定

#### 🤖 AI助手

好的，这是一个非常合理的改进。为了更好地组织输出文件，我们将添加一个配置选项来指定输出文件夹，并确保在保存任何文件之前创建该文件夹。

以下是更新后的代码，其中包含了输出文件夹的配置和处理：

```python
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def process_patient_data(file_path):
    \"\"\"
    读取单个患者的CSV文件并返回一个DataFrame，其中包含处理后的数据。
    \"\"\"
    df = pd.read_csv(file_path, index_col=0)
    # 将'天'列作为索引
    df.index.name = 'Day'
    return df

def generate_heatmap(data, title, cbar_label, cmap, vmin, vmax, ax, time_points=None):
    \"\"\"
    生成单个热图的通用函数。
    \"\"\"
    sns.heatmap(
        data,
        cmap=cmap,
        cbar=True,
        linewidths=0.5,
        linecolor='lightgray', # 使用更浅的网格线颜色，避免分散注意力
        fmt=\".0f\",
        annot=False,
        vmin=vmin,
        vmax=vmax,
        ax=ax,
        cbar_kws={\"label\": cbar_label, \"orientation\": \"vertical\", \"pad\": 0.03} # 调整颜色条标签和位置
    )
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Days (from -15 to 30)', fontsize=12)
    ax.set_ylabel('Variable Categories', fontsize=12)

    # 设置X轴刻度
    if time_points is not None:
        x_tick_labels = [str(day) if day % 5 == 0 else '' for day in time_points]
        ax.set_xticks(np.arange(len(time_points)) + 0.5)
        ax.set_xticklabels(x_tick_labels, rotation=45, ha='right', fontsize=10)
    ax.tick_params(axis='y', rotation=0, labelsize=10)


def analyze_and_visualize_data(data_frames, num_patients, config):
    \"\"\"
    分析数据可用性，导出CSV文件，并根据配置生成热图。
    \"\"\"
    # 确保输出文件夹存在
    if not os.path.exists(config['output_folder']):
        os.makedirs(config['output_folder'])
        print(f\"Created output folder: '{config['output_folder']}'\")

    # 定义变量分组
    variable_groups = {
        'CBC': [f'CBC{i:03d}' for i in range(1, 25)],
        'Inflammatory Biomarker': [f'Inflammatory Biomarker{i:03d}' for i in range(1, 10)],
        'VCN': ['VCN001'],
        'Lymphocyte Subsets': [f'Lymphocyte Subsets{i:03d}' for i in range(1, 12)],
        'Coagulation': [f'Coagulation{i:03d}' for i in range(1, 9)],
        'Electrolytes': [f'Electrolytes{i:03d}' for i in range(1, 7)],
        'Biochemistry': [f'Biochemistry{i:03d}' for i in range(1, 29)],
        'Vital Signs': [f'Vital Signs{i:03d}' for i in range(1, 7)]
    }

    time_points = range(-15, 31)
    availability_counts_matrix = pd.DataFrame(0, index=time_points, columns=variable_groups.keys())

    for df in data_frames:
        for day in time_points:
            if day in df.index:
                for group_name, variables in variable_groups.items():
                    available_in_group = False
                    for var in variables:
                        if var in df.columns and pd.notna(df.loc[day, var]):
                            available_in_group = True
                            break
                    if available_in_group:
                        availability_counts_matrix.loc[day, group_name] += 1

    # 计算可用性覆盖率（分数从 0 到 1）
    data_availability_fraction = (availability_counts_matrix / num_patients).T 

    # 计算缺失值百分比（0-100 整数）
    data_missing_percentage = ((1 - data_availability_fraction) * 100).astype(int)

    # 导出 CSV 文件
    if config['export_csv_availability']:
        output_availability_fraction_csv_path = os.path.join(config['output_folder'], f\"data_availability_fraction.{config['csv_export_format']}\")
        data_availability_fraction.to_csv(output_availability_fraction_csv_path)
        print(f\"Data availability fraction exported to '{output_availability_fraction_csv_path}'\")

    if config['export_csv_missing']:
        output_missing_percentage_csv_path = os.path.join(config['output_folder'], f\"data_missing_percentage.{config['csv_export_format']}\")
        data_missing_percentage.to_csv(output_missing_percentage_csv_path)
        print(f\"Data missing percentage (0-100) exported to '{output_missing_percentage_csv_path}'\")


    # 热图生成
    if config['generate_heatmap_availability'] or config['generate_heatmap_missing']:
        
        plt.style.use('seaborn-v0_8-whitegrid') # 尝试使用更专业的matplotlib样式
        
        if config['heatmap_layout'] == 'side_by_side' and config['generate_heatmap_availability'] and config['generate_heatmap_missing']:
            # 并排显示双热图
            fig, axes = plt.subplots(1, 2, figsize=config['figsize_double'], dpi=config['dpi'])
            
            # 覆盖率热图
            generate_heatmap(
                data_availability_fraction * 100,
                'Data Coverage (%)',
                'Coverage (%)',
                config['cmap_availability'],
                0, 100,
                ax=axes[0],
                time_points=time_points
            )
            
            # 缺失/缺口热图
            generate_heatmap(
                data_missing_percentage,
                'Missing Data (%)',
                'Missing (%)',
                config['cmap_missing'],
                0, 100,
                ax=axes[1],
                time_points=time_points
            )
            plt.tight_layout()
            output_file_path = os.path.join(config['output_folder'], f\"heatmap_coverage_and_missing_side_by_side.{config['output_format']}\")
            plt.savefig(output_file_path, format=config['output_format'])
            print(f\"Side-by-side heatmaps saved to '{output_file_path}'\")
            plt.show()

        else: # 单独显示或仅生成一个
            if config['generate_heatmap_availability']:
                fig, ax = plt.subplots(1, 1, figsize=config['figsize_single'], dpi=config['dpi'])
                generate_heatmap(
                    data_availability_fraction * 100,
                    'Data Coverage (%)',
                    'Coverage (%)',
                    config['cmap_availability'],
                    0, 100,
                    ax=ax,
                    time_points=time_points
                )
                plt.tight_layout()
                output_file_path = os.path.join(config['output_folder'], f\"heatmap_coverage.{config['output_format']}\")
                plt.savefig(output_file_path, format=config['output_format'])
                print(f\"Coverage heatmap saved to '{output_file_path}'\")
                plt.show()

            if config['generate_heatmap_missing']:
                fig, ax = plt.subplots(1, 1, figsize=config['figsize_single'], dpi=config['dpi'])
                generate_heatmap(
                    data_missing_percentage,
                    'Missing Data (%)',
                    'Missing (%)',
                    config['cmap_missing'],
                    0, 100,
                    ax=ax,
                    time_points=time_points
                )
                plt.tight_layout()
                output_file_path = os.path.join(config['output_folder'], f\"heatmap_missing.{config['output_format']}\")
                plt.savefig(output_file_path, format=config['output_format'])
                print(f\"Missing data heatmap saved to '{output_file_path}'\")
                plt.show()

if __name__ == \"__main__\":
    processed_folder = \"processed\"
    num_patients = 500
    all_patient_data = []

    # --- 配置选项 ---
    config = {
        # 输出文件夹
        'output_folder': 'output_results', # 所有生成的CSV和图像文件将保存到此文件夹

        # CSV 导出选项
        'export_csv_availability': True,  # 导出可用性分数 (0-1) CSV
        'export_csv_missing': True,       # 导出缺失百分比 (0-100 整数) CSV
        'csv_export_format': 'csv',       # CSV 导出格式 (例如: 'csv')

        # 热图生成选项
        'generate_heatmap_availability': True, # 生成覆盖率热图
        'generate_heatmap_missing': True,      # 生成缺失/缺口热图

        # 热图布局：'separate' (单独显示) 或 'side_by_side' (并排显示，仅当 generate_heatmap_availability 和 generate_heatmap_missing 都为 True 时有效)
        'heatmap_layout': 'side_by_side',  

        # 输出格式：'png', 'pdf', 'svg'
        'output_format': 'png',           

        # 配色方案选择
        'cmap_availability': 'viridis',    # 覆盖率热图的颜色映射 (0% 覆盖 -> 紫色, 100% 覆盖 -> 黄色)
        'cmap_missing': 'Blues',           # 缺失热图的颜色映射 (0% 缺失 -> 白色, 100% 缺失 -> 深蓝色)
                                           # 其他选择如 'RdYlGn_r' (红色-黄色-绿色 反转), 'YlOrRd' (黄-橙-红)

        # 图形大小和分辨率
        'figsize_single': (14, 8),         # 单个热图的图形大小 (宽, 高 英寸)
        'figsize_double': (24, 8),         # 并排热图的图形大小 (宽, 高 英寸)
        'dpi': 300,                        # 图像分辨率 (每英寸点数)
    }
    # ------------------

    # 确保'processed'文件夹存在
    if not os.path.exists(processed_folder):
        print(f\"Error: The folder '{processed_folder}' does not exist.\")
        print(\"Please create the folder and place the patient CSV files inside.\")
        exit()

    # 读取所有患者的数据
    print(f\"Reading data for {num_patients} patients from '{processed_folder}'...\")
    for i in range(1, num_patients + 1):
        file_name = f\"pt_{i}.csv\"
        file_path = os.path.join(processed_folder, file_name)
        if os.path.exists(file_path):
            df = process_patient_data(file_path)
            all_patient_data.append(df)
        else:
            print(f\"Warning: File '{file_path}' not found. Skipping patient {i}.\")

    if not all_patient_data:
        print(\"No patient data found. Exiting.\")
    else:
        print(\"All patient data loaded. Analyzing availability and generating output...\")
        analyze_and_visualize_data(all_patient_data, num_patients, config)
        print(\"Analysis complete based on configuration.\")

```

### 主要更改：

1.  **`config['output_folder']` 选项：**
    *   在 `config` 字典中添加了一个新的键 `'output_folder'`，其值为您希望保存所有输出文件的目录名称（例如 `'output_results'`）。

2.  **创建输出文件夹：**
    *   在 `analyze_and_visualize_data` 函数的开头，添加了以下代码：
        ```python
        if not os.path.exists(config['output_folder']):
            os.makedirs(config['output_folder'])
            print(f\"Created output folder: '{config['output_folder']}'\")
        ```
        这会检查指定的输出文件夹是否存在。如果不存在，它将使用 `os.makedirs()` 创建该文件夹。这将确保在尝试保存文件时不会出现错误。

3.  **使用 `os.path.join` 构建文件路径：**
    *   在保存所有 CSV 文件和热图图像时，不再直接拼接字符串文件名，而是使用 `os.path.join(config['output_folder'], filename)`。
    *   `os.path.join()` 是 Python 中处理文件路径的最佳实践，因为它会根据操作系统的不同（例如 Windows 使用 `\\`，Linux/macOS 使用 `/`）自动选择正确的路径分隔符。这使得代码在不同操作系统上更具可移植性。

现在，您只需修改 `config['output_folder']` 的值，所有生成的文件（CSV 和图像）都将自动保存到该指定的文件夹中，使得项目结构更加整洁和易于管理。

---

### 对话轮次 6

#### 👤 用户

INSERT_INPUT_HERE

---
