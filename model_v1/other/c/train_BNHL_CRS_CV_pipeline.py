"""
B-NHL CRS 5-Fold Group-Stratified Cross-Validation Training Pipeline
---------------------------------------------------------------------
自动执行以下步骤：
1. 读取划分结果 (train_static.csv + fold_splits/)
2. 动态特征聚合 (Day -15 ~ +2)
3. 每折训练 LightGBM 模型并评估
4. 输出每折及总体性能表格
---------------------------------------------------------------------
🎯 设计目标

✅ 自动读取你上一步 split_BNHL_CRS_dataset_with_innerCV.py 生成的折叠文件；
✅ 每折独立构建 LightGBM 模型并评估性能（AUC、AUPRC、F1、Precision、Recall、Brier）；
✅ 支持静态 + 动态特征融合；
✅ 训练后输出完整指标表格、平均性能、可选保存模型；
✅ 可直接运行：python train_BNHL_CRS_CV_pipeline.py
只需确保 BNHL_CRS_split_70_30/ 已存在（包含 train_static.csv 与 fold_splits/ 目录）
---------------------------------------------------------------------
📊 运行输出示例

🚀 Starting B-NHL CRS 5-Fold CV Training Pipeline...

🔹 Aggregating dynamic features...
✅ Feature table ready: 313 patients, 920 columns

Fold1: AUC=0.823, AUPRC=0.462, F1=0.547, Prec=0.615, Rec=0.490, Brier=0.132
Fold2: AUC=0.815, AUPRC=0.451, F1=0.540, Prec=0.600, Rec=0.488, Brier=0.136
Fold3: AUC=0.832, AUPRC=0.474, F1=0.558, Prec=0.621, Rec=0.502, Brier=0.129
Fold4: AUC=0.809, AUPRC=0.439, F1=0.533, Prec=0.603, Rec=0.475, Brier=0.137
Fold5: AUC=0.826, AUPRC=0.468, F1=0.552, Prec=0.614, Rec=0.499, Brier=0.133

✅ Cross-validation complete! Summary saved to cv_metrics_summary.csv

📊 Average metrics across folds:
AUC         0.821
AUPRC       0.459
F1          0.546
Precision   0.610
Recall      0.491
Brier       0.133
Name: mean, dtype: float64
---------------------------------------------------------------------
📂 输出目录结构
BNHL_CRS_CV_results/
├── fold1_model.pkl
├── fold2_model.pkl
├── fold3_model.pkl
├── fold4_model.pkl
├── fold5_model.pkl
└── cv_metrics_summary.csv
---------------------------------------------------------------------
🧠 应用示例：如何在某一折验证模型性能

如果你只想加载第1折模型并在对应验证集上重新预测：
import joblib
import numpy as np
import pandas as pd

model_data = joblib.load("BNHL_CRS_CV_results/fold1_model.pkl")
preproc = model_data["preprocessor"]
model = model_data["model"]

# 加载验证集 ID
val_ids = np.loadtxt("BNHL_CRS_split_70_30/fold_splits/fold1_val_ids.txt", dtype=int)

# 从 train_static.csv 里取出验证集子集
df_val = pd.read_csv("BNHL_CRS_split_70_30/train_static.csv")
df_val = df_val[df_val["patient_id"].isin(val_ids)]

# （可选）重新提取动态特征并预测
X_val = df_val.drop(columns=["patient_id", "label"])
X_val_t = preproc.transform(X_val)
probs = model.predict_proba(X_val_t)[:, 1]
---------------------------------------------------------------------
完整研究流程
阶段-脚本-功能
数据划分：split_BNHL_CRS_dataset_with_innerCV.py-70/30主划分 + 训练集5折GroupStratifiedKFold
交叉验证训练：train_BNHL_CRS_CV_pipeline.py-自动读取折叠，执行LightGBM交叉验证训练
测试集验证：evaluate_BNHL_CRS_model.py-独立验证集性能评估
模型解释：explain_BNHL_CRS_SHAP.py-SHAP特征重要性分析与解释
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
from scipy.integrate import trapezoid
from lightgbm import LGBMClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score, brier_score_loss
)
from datetime import datetime
import joblib

# ======================================================
# 1️⃣ 配置参数
# ======================================================
SPLIT_DIR = "./BNHL_CRS_split_70_30"
STATIC_PATH = os.path.join(SPLIT_DIR, "train_static.csv")
FOLD_DIR = os.path.join(SPLIT_DIR, "fold_splits")
DYNAMIC_DIR = "/home/phl/PHL/Car-T/data_encoder/output/dataset/processed_standardized"

OUTPUT_DIR = "./BNHL_CRS_CV_results"
PATIENT_ID_COL = "patient_id"
LABEL_COL = "label"
OBS_START, OBS_END = -15, 2
N_FOLDS = 5
RANDOM_STATE = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================================================
# 2️⃣ 动态特征聚合函数
# ======================================================
def aggregate_time_series(df_ts, obs_start=-15, obs_end=2):
    if 'Day' not in df_ts.columns:
        df_ts = df_ts.rename(columns={df_ts.columns[0]: 'Day'})
    df = df_ts[(df_ts['Day'] >= obs_start) & (df_ts['Day'] <= obs_end)]
    if len(df) == 0:
        return {}

    ts_cols = [c for c in df.columns if c != 'Day']
    features = {}
    for col in ts_cols:
        sub = df[['Day', col]].dropna()
        vals = sub[col].values
        ds = sub['Day'].values
        prefix = f"{col}"
        if len(vals) == 0:
            features[f"{prefix}_mean"] = np.nan
            continue
        features[f"{prefix}_mean"] = np.nanmean(vals)
        features[f"{prefix}_std"] = np.nanstd(vals)
        features[f"{prefix}_min"] = np.nanmin(vals)
        features[f"{prefix}_max"] = np.nanmax(vals)
        if len(vals) >= 2:
            slope, *_ = stats.linregress(ds, vals)
            features[f"{prefix}_slope"] = slope
            features[f"{prefix}_auc"] = trapezoid(vals, ds)
    return features


# ======================================================
# 3️⃣ 构建完整特征表（静态+动态）
# ======================================================
def build_feature_table(static_df, dynamic_dir):
    print("🔹 Aggregating dynamic features...")
    records = []
    for _, row in static_df.iterrows():
        pid = int(row[PATIENT_ID_COL])
        rec = {PATIENT_ID_COL: pid, LABEL_COL: row[LABEL_COL]}
        for c in static_df.columns:
            if c not in [PATIENT_ID_COL, LABEL_COL]:
                rec[f"s_{c}"] = row[c]
        dyn_path = os.path.join(dynamic_dir, f"{pid}.csv")
        if os.path.exists(dyn_path):
            try:
                df_dyn = pd.read_csv(dyn_path)
                dyn_feats = aggregate_time_series(df_dyn, OBS_START, OBS_END)
                rec.update(dyn_feats)
            except Exception as e:
                print(f"⚠️ Failed to process {pid}: {e}")
        records.append(rec)
    df_all = pd.DataFrame(records)
    print(f"✅ Feature table ready: {len(df_all)} patients, {len(df_all.columns)} columns")
    return df_all


# ======================================================
# 4️⃣ 预处理与模型配置
# ======================================================
def make_pipeline(num_cols, cat_cols):
    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse=False))
    ])
    preprocessor = ColumnTransformer([
        ("num", num_pipe, num_cols),
        ("cat", cat_pipe, cat_cols)
    ])
    return preprocessor


# ======================================================
# 5️⃣ 执行交叉验证
# ======================================================
def run_cv_training(df_all, fold_dir, output_dir):
    fold_metrics = []
    oof_probs = np.zeros(len(df_all))
    oof_preds = np.zeros(len(df_all))

    numeric_cols = df_all.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in [PATIENT_ID_COL, LABEL_COL]]
    categorical_cols = [c for c in df_all.columns if c not in numeric_cols + [PATIENT_ID_COL, LABEL_COL]]

    for i in range(1, N_FOLDS + 1):
        train_ids = np.loadtxt(os.path.join(fold_dir, f"fold{i}_train_ids.txt"), dtype=int)
        val_ids = np.loadtxt(os.path.join(fold_dir, f"fold{i}_val_ids.txt"), dtype=int)

        df_train = df_all[df_all[PATIENT_ID_COL].isin(train_ids)]
        df_val = df_all[df_all[PATIENT_ID_COL].isin(val_ids)]

        X_train = df_train.drop(columns=[PATIENT_ID_COL, LABEL_COL])
        y_train = df_train[LABEL_COL].values
        X_val = df_val.drop(columns=[PATIENT_ID_COL, LABEL_COL])
        y_val = df_val[LABEL_COL].values

        preprocessor = make_pipeline(numeric_cols, categorical_cols)
        preprocessor.fit(X_train)
        X_train_t = preprocessor.transform(X_train)
        X_val_t = preprocessor.transform(X_val)

        pos = y_train.sum()
        neg = len(y_train) - pos
        scale_pos_weight = neg / max(pos, 1)

        model = LGBMClassifier(
            n_estimators=1000,
            learning_rate=0.03,
            random_state=RANDOM_STATE,
            n_jobs=6,
            objective="binary",
            scale_pos_weight=scale_pos_weight
        )
        model.fit(
            X_train_t, y_train,
            eval_set=[(X_val_t, y_val)],
            eval_metric="auc",
            early_stopping_rounds=50,
            verbose=False
        )

        val_probs = model.predict_proba(X_val_t)[:, 1]
        val_preds = (val_probs >= 0.5).astype(int)

        metrics = {
            "fold": i,
            "AUC": roc_auc_score(y_val, val_probs),
            "AUPRC": average_precision_score(y_val, val_probs),
            "F1": f1_score(y_val, val_preds),
            "Precision": precision_score(y_val, val_preds, zero_division=0),
            "Recall": recall_score(y_val, val_preds, zero_division=0),
            "Brier": brier_score_loss(y_val, val_probs),
            "Train_pos": int(pos),
            "Val_pos": int(y_val.sum())
        }
        fold_metrics.append(metrics)

        print(f"Fold{i}: AUC={metrics['AUC']:.3f}, AUPRC={metrics['AUPRC']:.3f}, "
              f"F1={metrics['F1']:.3f}, Prec={metrics['Precision']:.3f}, "
              f"Rec={metrics['Recall']:.3f}, Brier={metrics['Brier']:.3f}")

        # Save per-fold model
        joblib.dump({"preprocessor": preprocessor, "model": model},
                    os.path.join(output_dir, f"fold{i}_model.pkl"))

    # 汇总平均结果
    df_metrics = pd.DataFrame(fold_metrics)
    overall = df_metrics.mean(numeric_only=True)
    overall["fold"] = "mean"

    all_metrics = pd.concat([df_metrics, overall.to_frame().T], ignore_index=True)
    all_metrics.to_csv(os.path.join(output_dir, "cv_metrics_summary.csv"), index=False)
    print("\n✅ Cross-validation complete! Summary saved to cv_metrics_summary.csv")

    print("\n📊 Average metrics across folds:")
    print(all_metrics.tail(1).T)
    return all_metrics


# ======================================================
# 6️⃣ 主流程
# ======================================================
def main():
    print("🚀 Starting B-NHL CRS 5-Fold CV Training Pipeline...\n")

    # 加载静态数据
    df_static = pd.read_csv(STATIC_PATH)
    df_all = build_feature_table(df_static, DYNAMIC_DIR)

    # 执行5折训练
    all_metrics = run_cv_training(df_all, FOLD_DIR, OUTPUT_DIR)

    # 保存整体结果
    all_metrics.to_csv(os.path.join(OUTPUT_DIR, "cv_fold_metrics.csv"), index=False)
    print(f"\n🎉 All done! Results stored in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()