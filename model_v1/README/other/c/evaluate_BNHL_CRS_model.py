"""
验证集性能评估脚本
Evaluate trained B-NHL CRS model on independent test set
-------------------------------------------------------
- Loads LightGBM pipeline (.pkl)
- Loads test_static.csv + test_dynamic/
- Aggregates dynamic features (Day -15~+2)
- Applies model pipeline
- Outputs performance metrics + curves
-------------------------------------------------------
✅ 功能概述：
	•	自动加载模型文件：BNHL_CRS_model_output/BNHL_CRS_LGBM_pipeline.pkl
	•	自动加载测试集：BNHL_CRS_split_70_30/test_static.csv + test_dynamic/
	•	使用与训练一致的聚合逻辑（Day -15 ~ +2）提取动态特征
	•	进行推理并输出：
	•	ROC-AUC、PR-AUC、F1、Precision、Recall、Brier
	•	校准曲线、ROC 曲线、PR 曲线（保存 PNG）
	•	predictions_test.csv（含预测概率与标签）
-------------------------------------------------------
✅ 生成结果目录
BNHL_CRS_evaluation/
├── predictions_test.csv
├── test_metrics.csv
├── ROC_curve.png
└── PR_curve.png
-------------------------------------------------------
📊 输出示例
📊 Test set metrics:
  AUC: 0.8124
  AUPRC: 0.4317
  Precision: 0.6000
  Recall: 0.4211
  F1: 0.4941
  Brier: 0.1328
-------------------------------------------------------
🧠 验证后推荐

✅ 若指标接近交叉验证平均值（±0.05 以内）→ 模型泛化良好
⚠️ 若差距 >0.1 → 需检查时间泄漏、样本量、分布漂移等。
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, average_precision_score, precision_score, recall_score,
    f1_score, brier_score_loss, roc_curve, precision_recall_curve
)
import matplotlib.pyplot as plt
from scipy import stats
from scipy.integrate import trapezoid

# ======================================================
# 1. PATHS
# ======================================================
SPLIT_DIR = "./BNHL_CRS_split_70_30"
MODEL_PATH = "./BNHL_CRS_model_output/BNHL_CRS_LGBM_pipeline.pkl"
STATIC_TEST = os.path.join(SPLIT_DIR, "test_static.csv")
DYNAMIC_TEST_DIR = os.path.join(SPLIT_DIR, "test_dynamic")
OUTPUT_DIR = "./BNHL_CRS_evaluation"

PATIENT_ID_COL = "patient_id"
LABEL_COL = "label"
OBS_START, OBS_END = -15, 2

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================================================
# 2. LOAD MODEL
# ======================================================
print("🔹 Loading trained pipeline...")
pipeline_data = joblib.load(MODEL_PATH)
preprocessor = pipeline_data["preprocessor"]
model = pipeline_data["model"]

# ======================================================
# 3. LOAD TEST STATIC + DYNAMIC
# ======================================================
df_static = pd.read_csv(STATIC_TEST)
print(f"Loaded {len(df_static)} patients in test set")

# --------------------
# Dynamic aggregation
# --------------------
def aggregate_time_series(df_ts: pd.DataFrame, obs_start=-15, obs_end=2):
    if 'Day' not in df_ts.columns:
        df_ts = df_ts.rename(columns={df_ts.columns[0]: 'Day'})
    df = df_ts[(df_ts['Day'] >= obs_start) & (df_ts['Day'] <= obs_end)]
    if len(df) == 0:
        return {}
    features = {}
    ts_cols = [c for c in df.columns if c != 'Day']
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

records = []
missing = []
for _, row in df_static.iterrows():
    pid = int(row[PATIENT_ID_COL])
    rec = {PATIENT_ID_COL: pid, LABEL_COL: row[LABEL_COL]}
    for c in df_static.columns:
        if c not in [PATIENT_ID_COL, LABEL_COL]:
            rec[f"s_{c}"] = row[c]
    dyn_path = os.path.join(DYNAMIC_TEST_DIR, f"{pid}.csv")
    if os.path.exists(dyn_path):
        try:
            df_dyn = pd.read_csv(dyn_path)
            dyn_feats = aggregate_time_series(df_dyn, OBS_START, OBS_END)
            rec.update(dyn_feats)
        except Exception as e:
            print(f"⚠️ Failed to process {pid}: {e}")
            missing.append(pid)
    else:
        missing.append(pid)
    records.append(rec)

df_test = pd.DataFrame(records)
print(f"✅ Feature table ready: {len(df_test)} rows, {len(df_test.columns)} cols")

# ======================================================
# 4. APPLY PIPELINE
# ======================================================
X_test = df_test.drop(columns=[LABEL_COL, PATIENT_ID_COL])
y_test = df_test[LABEL_COL].values
X_test_t = preprocessor.transform(X_test)

probs = model.predict_proba(X_test_t)[:, 1]
preds = (probs >= 0.5).astype(int)

# ======================================================
# 5. METRICS
# ======================================================
metrics = {
    "AUC": roc_auc_score(y_test, probs),
    "AUPRC": average_precision_score(y_test, probs),
    "Precision": precision_score(y_test, preds, zero_division=0),
    "Recall": recall_score(y_test, preds, zero_division=0),
    "F1": f1_score(y_test, preds, zero_division=0),
    "Brier": brier_score_loss(y_test, probs)
}
print("\n📊 Test set metrics:")
for k, v in metrics.items():
    print(f"  {k}: {v:.4f}")

# ======================================================
# 6. SAVE PREDICTIONS
# ======================================================
df_out = df_test[[PATIENT_ID_COL, LABEL_COL]].copy()
df_out["probability"] = probs
df_out["prediction"] = preds
df_out.to_csv(os.path.join(OUTPUT_DIR, "predictions_test.csv"), index=False)
print("✅ Predictions saved: predictions_test.csv")

# ======================================================
# 7. PLOTS
# ======================================================
fpr, tpr, _ = roc_curve(y_test, probs)
prec, rec, _ = precision_recall_curve(y_test, probs)

plt.figure()
plt.plot(fpr, tpr)
plt.xlabel("False Positive Rate"); plt.ylabel("True Positive Rate")
plt.title(f"ROC Curve (AUC={metrics['AUC']:.3f})")
plt.savefig(os.path.join(OUTPUT_DIR, "ROC_curve.png"), dpi=200)

plt.figure()
plt.plot(rec, prec)
plt.xlabel("Recall"); plt.ylabel("Precision")
plt.title(f"PR Curve (AUPRC={metrics['AUPRC']:.3f})")
plt.savefig(os.path.join(OUTPUT_DIR, "PR_curve.png"), dpi=200)

print("📈 ROC & PR curves saved.")

# ======================================================
# 8. SAVE METRICS
# ======================================================
pd.DataFrame([metrics]).to_csv(os.path.join(OUTPUT_DIR, "test_metrics.csv"), index=False)
print("📄 Metrics file saved: test_metrics.csv")
print(f"\n🎉 Evaluation complete. Results stored in: {OUTPUT_DIR}")