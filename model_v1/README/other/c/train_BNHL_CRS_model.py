"""
Train LightGBM model for B-NHL CRS severity prediction
-----------------------------------------------------
Uses train_static.csv + train_dynamic/ from previous split step.
Pipeline steps:
- Aggregate dynamic features (Day -15~+2)
- Merge static + dynamic
- Handle missing values
- Encode categoricals, scale numericals
- 5-fold stratified CV
- LightGBM model with class balancing
- Evaluate (AUC, AUPRC, F1, Brier)
-----------------------------------------------------
预测 B-NHL 患者严重 CRS（二分类）
使用 train_static.csv + train_dynamic/ 数据，自动完成：
	•	动态时间窗聚合特征生成（Day -15 ~ +2）
	•	静态 + 动态特征融合
	•	缺失值插补（折内安全）
	•	标准化、编码
	•	5 折分层交叉验证
	•	LightGBM 模型训练与评估（AUC, AUPRC, F1, 校准）
	•	最终模型保存（.pkl pipeline）
-----------------------------------------------------
执行后生成的结构
BNHL_CRS_model_output/
├── BNHL_CRS_LGBM_pipeline.pkl     # 完整 pipeline（预处理+模型）
├── cv_fold_metrics.csv            # 每折指标
├── cv_overall_metrics.csv         # 平均指标
-----------------------------------------------------
说明与建议
aggregate_time_series()：统计 + 趋势 + AUC + 峰值时间，可轻松扩展如“异常天数”等指标
preprocessor：折内拟合插补与标准化（无泄漏）
StratifiedKFold：保证严重CRS比例一致
LightGBM：自适应 scale_pos_weight = neg/pos，对轻度不平衡数据更稳健
指标：AUC + AUPRC + F1 + 校准（Brier）——适合临床预测研究
模型保存：.pkl 文件中含 preprocessor，后续推理阶段可直接 predict_proba()
-----------------------------------------------------
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
from scipy.integrate import trapezoid
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score, brier_score_loss
)
from lightgbm import LGBMClassifier
import joblib
from datetime import datetime

# ======================================================
# 1. PATH CONFIGURATION
# ======================================================
SPLIT_DIR = "./BNHL_CRS_split_70_30"
STATIC_TRAIN = os.path.join(SPLIT_DIR, "train_static.csv")
DYNAMIC_TRAIN_DIR = os.path.join(SPLIT_DIR, "train_dynamic")
OUTPUT_DIR = "./BNHL_CRS_model_output"
PATIENT_ID_COL = "patient_id"
LABEL_COL = "label"
OBS_START, OBS_END = -15, 2
N_SPLITS = 5
RANDOM_STATE = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================================================
# 2. TIME-SERIES AGGREGATION FUNCTION
# ======================================================
def aggregate_time_series(df_ts: pd.DataFrame, obs_start=-15, obs_end=2):
    """
    Aggregate patient's dynamic data within observation window.
    """
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
            # empty column -> fill with NaN
            stats_dict = {f"{prefix}_mean": np.nan, f"{prefix}_std": np.nan,
                          f"{prefix}_min": np.nan, f"{prefix}_max": np.nan,
                          f"{prefix}_slope": np.nan, f"{prefix}_auc": np.nan,
                          f"{prefix}_time_to_peak": np.nan, f"{prefix}_count": 0}
        else:
            # descriptive stats
            stats_dict = {
                f"{prefix}_mean": np.nanmean(vals),
                f"{prefix}_std": np.nanstd(vals, ddof=0),
                f"{prefix}_min": np.nanmin(vals),
                f"{prefix}_max": np.nanmax(vals),
                f"{prefix}_count": len(vals)
            }
            # slope
            if len(vals) >= 2:
                slope, *_ = stats.linregress(ds, vals)
                stats_dict[f"{prefix}_slope"] = slope
                stats_dict[f"{prefix}_auc"] = trapezoid(vals, ds)
                stats_dict[f"{prefix}_time_to_peak"] = ds[np.argmax(vals)]
            else:
                stats_dict[f"{prefix}_slope"] = np.nan
                stats_dict[f"{prefix}_auc"] = np.nan
                stats_dict[f"{prefix}_time_to_peak"] = np.nan
        features.update(stats_dict)
    return features

# ======================================================
# 3. LOAD STATIC + DYNAMIC DATA
# ======================================================
print("🔹 Loading static training data...")
df_static = pd.read_csv(STATIC_TRAIN)
print(f"Total patients (static): {len(df_static)}")

print("🔹 Aggregating dynamic features...")
records = []
missing_files = []
for _, row in df_static.iterrows():
    pid = int(row[PATIENT_ID_COL])
    dyn_path = os.path.join(DYNAMIC_TRAIN_DIR, f"{pid}.csv")
    rec = {PATIENT_ID_COL: pid, LABEL_COL: row[LABEL_COL]}
    # add static vars
    for c in df_static.columns:
        if c not in [PATIENT_ID_COL, LABEL_COL]:
            rec[f"s_{c}"] = row[c]

    if os.path.exists(dyn_path):
        try:
            df_dyn = pd.read_csv(dyn_path)
            dyn_feats = aggregate_time_series(df_dyn, OBS_START, OBS_END)
            rec.update(dyn_feats)
        except Exception as e:
            print(f"⚠️ Failed to process {dyn_path}: {e}")
            missing_files.append(pid)
    else:
        missing_files.append(pid)

    records.append(rec)

df_all = pd.DataFrame(records)
print(f"✅ Aggregation complete: {len(df_all)} patients, {len(df_all.columns)} total columns")

# ======================================================
# 4. PREPROCESSING PIPELINE
# ======================================================
numeric_cols = df_all.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols = [c for c in numeric_cols if c not in [PATIENT_ID_COL, LABEL_COL]]
categorical_cols = [c for c in df_all.columns if c not in numeric_cols + [PATIENT_ID_COL, LABEL_COL]]

num_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

cat_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse=False))
])

preprocessor = ColumnTransformer([
    ("num", num_pipe, numeric_cols),
    ("cat", cat_pipe, categorical_cols)
])

# ======================================================
# 5. MODEL & CV CONFIGURATION
# ======================================================
lgb = LGBMClassifier(
    n_estimators=1000,
    learning_rate=0.03,
    max_depth=-1,
    random_state=RANDOM_STATE,
    n_jobs=6,
    objective="binary",
    metric="None"
)

skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

X = df_all.drop(columns=[LABEL_COL, PATIENT_ID_COL])
y = df_all[LABEL_COL].values

oof_preds, oof_probs = np.zeros(len(y)), np.zeros(len(y))
fold_metrics = []

# ======================================================
# 6. CROSS-VALIDATION LOOP
# ======================================================
print("\n🚀 Starting 5-fold Stratified CV...")
for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]

    # compute scale_pos_weight
    pos = y_train.sum()
    neg = len(y_train) - pos
    scale_pos_weight = neg / max(pos, 1)
    lgb.set_params(scale_pos_weight=scale_pos_weight)

    # fit preprocessor
    preprocessor.fit(X_train)
    X_train_t = preprocessor.transform(X_train)
    X_val_t = preprocessor.transform(X_val)

    # fit model
    lgb.fit(
        X_train_t, y_train,
        eval_set=[(X_val_t, y_val)],
        eval_metric="auc",
        early_stopping_rounds=50,
        verbose=False
    )

    val_probs = lgb.predict_proba(X_val_t)[:, 1]
    val_preds = (val_probs >= 0.5).astype(int)

    # metrics
    roc = roc_auc_score(y_val, val_probs)
    pr = average_precision_score(y_val, val_probs)
    f1 = f1_score(y_val, val_preds)
    prec = precision_score(y_val, val_preds, zero_division=0)
    rec = recall_score(y_val, val_preds, zero_division=0)
    brier = brier_score_loss(y_val, val_probs)

    oof_preds[val_idx] = val_preds
    oof_probs[val_idx] = val_probs

    fold_metrics.append({
        "fold": fold, "roc_auc": roc, "pr_auc": pr,
        "f1": f1, "precision": prec, "recall": rec, "brier": brier,
        "pos_train": int(pos), "neg_train": int(neg)
    })

    print(f"Fold {fold} | AUC={roc:.3f}, AUPRC={pr:.3f}, F1={f1:.3f}, "
          f"Prec={prec:.3f}, Rec={rec:.3f}, Brier={brier:.3f}")

# ======================================================
# 7. OVERALL METRICS
# ======================================================
overall = {
    "AUC": roc_auc_score(y, oof_probs),
    "AUPRC": average_precision_score(y, oof_probs),
    "F1": f1_score(y, oof_preds),
    "Precision": precision_score(y, oof_preds, zero_division=0),
    "Recall": recall_score(y, oof_preds, zero_division=0),
    "Brier": brier_score_loss(y, oof_probs)
}
print("\n📊 Overall CV results:")
for k, v in overall.items():
    print(f"  {k}: {v:.4f}")

# ======================================================
# 8. SAVE FINAL MODEL (TRAINED ON FULL DATA)
# ======================================================
print("\n🧩 Training final model on full data...")
preprocessor.fit(X)
X_t = preprocessor.transform(X)
pos, neg = y.sum(), len(y) - y.sum()
lgb_final = LGBMClassifier(
    n_estimators=1000,
    learning_rate=0.03,
    random_state=RANDOM_STATE,
    n_jobs=6,
    scale_pos_weight=neg / max(pos, 1),
    objective="binary"
)
lgb_final.fit(X_t, y)

joblib.dump(
    {"preprocessor": preprocessor, "model": lgb_final, "cv_metrics": fold_metrics, "overall": overall},
    os.path.join(OUTPUT_DIR, "BNHL_CRS_LGBM_pipeline.pkl")
)
print(f"\n✅ Final model saved: {OUTPUT_DIR}/BNHL_CRS_LGBM_pipeline.pkl")

# ======================================================
# 9. SAVE METRICS
# ======================================================
metrics_df = pd.DataFrame(fold_metrics)
metrics_df.to_csv(os.path.join(OUTPUT_DIR, "cv_fold_metrics.csv"), index=False)
overall_df = pd.DataFrame([overall])
overall_df.to_csv(os.path.join(OUTPUT_DIR, "cv_overall_metrics.csv"), index=False)

print("\n🎉 Training complete. Metrics saved in model_output folder.")