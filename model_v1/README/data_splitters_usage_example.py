"""
数据分割器使用示例
==================

演示如何使用 data_splitters.py 中的类来替代原有的 train_test_split

作者: AI Assistant  
日期: 2025-11-20
"""

import pandas as pd
import numpy as np
from data_splitters import (
    PatientLevelStratifiedSplitter,
    PatientLevelStratifiedSplitterWithCV,
    patient_level_train_test_split
)
from perfect_pipeline import build_no_leak_pipeline


# ============================================================
# 示例1: 基础用法 - 替代 train_test_split
# ============================================================

def example_1_basic_split():
    """
    演示如何用PatientLevelStratifiedSplitter替代train_test_split
    """
    print("=" * 70)
    print("示例1: 基础患者级分层分割")
    print("=" * 70)
    
    # 读取数据
    df = pd.read_csv("encoded_standardized.csv")
    
    # 毒性二元化（如需要）
    df["label"] = (df["infection_grade"] > 2).astype(int)
    
    # ========== 原始代码 ==========
    # from sklearn.model_selection import train_test_split
    # train_df, test_df = train_test_split(
    #     df, test_size=0.3, stratify=df["label"], random_state=42
    # )
    
    # ========== 新代码：方式1 - 使用类 ==========
    splitter = PatientLevelStratifiedSplitter(test_size=0.3, random_state=42)
    train_df, test_df = splitter.split(
        df, 
        label_col="label", 
        patient_id_col="patient_id"  # 确保患者级独立性
    )
    
    # ========== 新代码：方式2 - 使用兼容函数（更简单）==========
    # train_df, test_df = patient_level_train_test_split(
    #     df,
    #     label_col="label",
    #     patient_id_col="patient_id",
    #     test_size=0.3,
    #     random_state=42
    # )
    
    print(f"\n训练集大小: {len(train_df)}")
    print(f"测试集大小: {len(test_df)}")
    
    return train_df, test_df


# ============================================================
# 示例2: 带交叉验证的完整训练流程
# ============================================================

def example_2_with_cross_validation():
    """
    演示如何使用PatientLevelStratifiedSplitterWithCV进行交叉验证
    """
    print("\n" + "=" * 70)
    print("示例2: 患者级分层分割 + 5折交叉验证")
    print("=" * 70)
    
    # 读取数据
    df = pd.read_csv("encoded_standardized.csv")
    df["label"] = (df["infection_grade"] > 2).astype(int)
    
    # 使用带CV的分割器
    splitter = PatientLevelStratifiedSplitterWithCV(
        test_size=0.3, 
        n_folds=5, 
        random_state=42
    )
    
    train_df, test_df, cv_folds = splitter.split(
        df, 
        label_col="label", 
        patient_id_col="patient_id"
    )
    
    # 定义特征列
    numeric_cols = ["age", "bm_disease_burden"]
    categorical_cols = ["sex", "bridging_therapy"]
    ordinal_cols = ["ann_arbor_stage"]
    dynamic_dir = "/home/.../processed_standardized/"
    
    # 构建Pipeline
    pipe = build_no_leak_pipeline(
        numeric_cols, categorical_cols, ordinal_cols, dynamic_dir
    )
    
    # 方法A: 使用整个训练集进行训练（不使用CV）
    print("\n方法A: 直接在整个训练集上训练")
    pipe.fit(train_df, train_df["label"])
    test_pred = pipe.predict_proba(test_df)[:, 1]
    print(f"测试集预测完成，形状: {test_pred.shape}")
    
    # 方法B: 使用交叉验证进行超参数调优或稳定性评估
    print("\n方法B: 使用5折交叉验证")
    cv_scores = []
    
    for fold_idx, (train_patient_ids, val_patient_ids) in enumerate(cv_folds, 1):
        print(f"\n--- Fold {fold_idx} ---")
        
        # 根据患者ID筛选数据
        fold_train = train_df[train_df["patient_id"].isin(train_patient_ids)]
        fold_val = train_df[train_df["patient_id"].isin(val_patient_ids)]
        
        print(f"Fold训练集: {len(fold_train)}, 验证集: {len(fold_val)}")
        
        # 在当前fold上训练
        pipe_fold = build_no_leak_pipeline(
            numeric_cols, categorical_cols, ordinal_cols, dynamic_dir
        )
        pipe_fold.fit(fold_train, fold_train["label"])
        
        # 在验证集上评估
        val_pred = pipe_fold.predict_proba(fold_val)[:, 1]
        
        # 计算评估指标（这里以AUC为例）
        from sklearn.metrics import roc_auc_score
        auc = roc_auc_score(fold_val["label"], val_pred)
        cv_scores.append(auc)
        print(f"Fold {fold_idx} AUC: {auc:.4f}")
    
    print(f"\n平均CV AUC: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
    
    # 最终在整个训练集上重新训练，并在测试集上评估
    print("\n最终模型训练（使用完整训练集）...")
    final_pipe = build_no_leak_pipeline(
        numeric_cols, categorical_cols, ordinal_cols, dynamic_dir
    )
    final_pipe.fit(train_df, train_df["label"])
    final_test_pred = final_pipe.predict_proba(test_df)[:, 1]
    final_auc = roc_auc_score(test_df["label"], final_test_pred)
    print(f"最终测试集 AUC: {final_auc:.4f}")
    
    return train_df, test_df, cv_folds


# ============================================================
# 示例3: 在 model.py 中直接使用
# ============================================================

def example_3_model_py_integration():
    """
    演示如何在model.py中集成（第11行替换）
    """
    print("\n" + "=" * 70)
    print("示例3: model.py 集成示例")
    print("=" * 70)
    
    # ========== 原始 model.py 第11行左右的代码 ==========
    # from sklearn.model_selection import train_test_split
    # train_df, test_df = train_test_split(df, test_size=0.3, 
    #                                      stratify=df["label"], random_state=42)
    
    # ========== 修改后的代码 ==========
    # 在文件顶部添加导入
    # from pipeline.data_splitters import patient_level_train_test_split
    
    # 然后在第11行附近替换为：
    df = pd.read_csv("encoded_standardized.csv")
    df["label"] = (df["infection_grade"] > 2).astype(int)
    
    train_df, test_df = patient_level_train_test_split(
        df,
        label_col="label",
        patient_id_col="patient_id",  # 新增：指定患者ID列
        test_size=0.3,
        random_state=42
    )
    
    # 后续代码保持不变
    print(f"训练集: {len(train_df)}, 测试集: {len(test_df)}")
    print("✅ 成功替换 train_test_split，确保患者级独立性！")


# ============================================================
# 示例4: 保存和加载折叠信息（用于复现实验）
# ============================================================

def example_4_save_load_folds():
    """
    演示如何保存和加载CV折叠信息，确保实验可复现
    """
    print("\n" + "=" * 70)
    print("示例4: 保存和加载CV折叠信息")
    print("=" * 70)
    
    import os
    
    df = pd.read_csv("encoded_standardized.csv")
    df["label"] = (df["infection_grade"] > 2).astype(int)
    
    # 创建分割
    splitter = PatientLevelStratifiedSplitterWithCV(
        test_size=0.3, n_folds=5, random_state=42
    )
    train_df, test_df, cv_folds = splitter.split(
        df, label_col="label", patient_id_col="patient_id"
    )
    
    # 保存折叠信息
    output_dir = "./output/cv_folds"
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存训练集和测试集ID
    train_df["patient_id"].to_csv(
        os.path.join(output_dir, "train_ids.txt"), 
        index=False, header=False
    )
    test_df["patient_id"].to_csv(
        os.path.join(output_dir, "test_ids.txt"), 
        index=False, header=False
    )
    
    # 保存每一折的ID
    for i, (train_ids, val_ids) in enumerate(cv_folds, 1):
        np.savetxt(
            os.path.join(output_dir, f"fold{i}_train_ids.txt"), 
            train_ids, fmt="%s"
        )
        np.savetxt(
            os.path.join(output_dir, f"fold{i}_val_ids.txt"), 
            val_ids, fmt="%s"
        )
    
    print(f"\n✅ 折叠信息已保存到: {output_dir}")
    print(f"   - train_ids.txt, test_ids.txt")
    print(f"   - fold1-5_train_ids.txt, fold1-5_val_ids.txt")
    
    # 加载折叠信息（用于复现）
    print("\n从文件加载折叠信息...")
    loaded_train_ids = pd.read_csv(
        os.path.join(output_dir, "train_ids.txt"), 
        header=None
    )[0].values
    
    fold1_train_ids = np.loadtxt(
        os.path.join(output_dir, "fold1_train_ids.txt"), 
        dtype=int
    )
    
    print(f"加载的训练集ID数: {len(loaded_train_ids)}")
    print(f"加载的Fold1训练ID数: {len(fold1_train_ids)}")


# ============================================================
# 主函数
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("数据分割器使用示例集")
    print("=" * 70)
    
    # 运行各个示例（注释掉不需要的）
    
    # example_1_basic_split()
    # example_2_with_cross_validation()
    example_3_model_py_integration()
    # example_4_save_load_folds()
    
    print("\n" + "=" * 70)
    print("✅ 所有示例运行完成！")
    print("=" * 70)
