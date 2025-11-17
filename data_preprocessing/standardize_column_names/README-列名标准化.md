# 列名标准化工具使用说明

## 功能
将CSV文件中包含空格的列名替换为下划线格式。

## 快速使用

### 1. 使用默认文件路径
```bash
cd /home/phl/PHL/Car-T/data_preprocessing
python standardize_column_names.py
```

### 2. 指定输入文件
```bash
python standardize_column_names.py /path/to/input.csv
```

### 3. 指定输入和输出文件
```bash
python standardize_column_names.py /path/to/input.csv /path/to/output.csv
```

## 自定义列名映射

编辑 `standardize_column_names.py` 中的 `CUSTOM_MAPPINGS` 字典：

```python
CUSTOM_MAPPINGS = {
    "BM disease burden": "BM_Disease_Burden",  # 自定义大小写
    "CRS grade": "CRS_Grade",
    # 添加更多自定义映射...
}
```

## 处理结果

已成功处理 19 个包含空格的列名：

| 原列名 | 新列名 |
|--------|--------|
| BM disease burden | BM_disease_burden |
| Bone marrow cellularity | Bone_marrow_cellularity |
| extramedullary mass | extramedullary_mass |
| extranodal involvement | extranodal_involvement |
| B symptoms | B_symptoms |
| Ann Arbor stage | Ann_Arbor_stage |
| Number of prior therapy lines | Number_of_prior_therapy_lines |
| Prior hematopoietic stem cell | Prior_hematopoietic_stem_cell |
| Prior CAR-T therapy | Prior_CAR-T_therapy |
| Bridging therapy | Bridging_therapy |
| CAR-T therapy following auto-HSCT | CAR-T_therapy_following_auto-HSCT |
| Costimulatory molecule | Costimulatory_molecule |
| Type of construct(tandem/single target) | Type_of_construct(tandem/single_target) |
| CAR-T cell infusion date | CAR-T_cell_infusion_date |
| CRS grade | CRS_grade |
| ICANS grade | ICANS_grade |
| Early ICAHT grade | Early_ICAHT_grade |
| Late ICAHT grade | Late_ICAHT_grade |
| Infection grade | Infection_grade |

## 验证

```bash
# 检查是否还有空格
head -n 1 /home/phl/PHL/Car-T/datasetcart/encoded.csv | tr ',' '\n' | grep " "
```

✅ 结果：所有列名已标准化，无空格
