"""
SHAP 解释与特征可视化脚本
SHAP-based feature interpretation for B-NHL CRS model
-----------------------------------------------------
- Loads saved pipeline (.pkl)
- Computes SHAP values on training data
- Saves summary plots & top feature CSV
-----------------------------------------------------
✅ 功能：
	•	加载训练好的 BNHL_CRS_LGBM_pipeline.pkl
	•	自动获取 feature names（预处理后）
	•	计算 SHAP 值（使用 TreeExplainer）
	•	输出：
	•	shap_values_summary.png（全局重要性）
	•	shap_summary_bar.png（平均绝对影响力前 20）
	•	shap_top_features.csv（Top-N 特征重要性）
	•	可选个体解释（force plot，示例 1 位严重CRS病人）
-----------------------------------------------------
 输出目录结构
BNHL_CRS_SHAP_output/
├── shap_values_summary.png       # SHAP散点汇总图
├── shap_summary_bar.png          # 平均绝对影响力条形图
├── shap_top_features.csv         # 前20重要特征
└── force_plot_example.html       # 单病人解释（可交互）
-----------------------------------------------------
SHAP 解释使用建议
summary_plot：显示全局主要特征及影响方向（红→正向提高严重CRS风险）
bar_plot：特征平均影响力排名，选前 10–20 个用于报告
force_plot：单个病人解释，展示哪些特征导致高风险预测
mean_abs_shap：可导出为 CSV，用于科研报告或特征筛选复现
-----------------------------------------------------
"""

import os
import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt

# ======================================================
# 1. PATHS
# ======================================================
MODEL_PATH = "./BNHL_CRS_model_output/BNHL_CRS_LGBM_pipeline.pkl"
SPLIT_DIR = "./BNHL_CRS_split_70_30"
TRAIN_STATIC = os.path.join(SPLIT_DIR, "train_static.csv")
TRAIN_DYNAMIC = os.path.join(SPLIT_DIR, "train_dynamic")
OUTPUT_DIR = "./BNHL_CRS_SHAP_output"

PATIENT_ID_COL = "patient_id"
LABEL_COL = "label"
OBS_START, OBS_END = -15, 2
TOP_N = 20

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================================================
# 2. LOAD MODEL
# ======================================================
print("🔹 Loading pipeline...")
pipeline_data = joblib.load(MODEL_PATH)
model = pipeline_data["model"]
preprocessor = pipeline_data["preprocessor"]

# ======================================================
# 3. LOAD TRAIN DATA (FEATURE TABLE)
# ======================================================
feature_path = "./BNHL_CRS_model_output/cv_overall_metrics.csv"  # optional
# 或重新生成训练特征表 (若你已保存可直接载入 patient_feature_table)
print("🔹 Loading aggregated training features for SHAP analysis...")
train_feature_file = "./BNHL_CRS_model_output/train_features_used.csv"
if not os.path.exists(train_feature_file):
    print("⚠️ 没有缓存特征文件，将从 pipeline 的 preprocessor 获取 feature names。")
else:
    df_all = pd.read_csv(train_feature_file)
    X = df_all.drop(columns=[PATIENT_ID_COL, LABEL_COL])
    y = df_all[LABEL_COL].values
    X_t = preprocessor.transform(X)

# ======================================================
# 4. FEATURE NAMES
# ======================================================
print("🔹 Extracting feature names...")
num_features = preprocessor.named_transformers_["num"].get_feature_names_out()
cat_features = preprocessor.named_transformers_["cat"].get_feature_names_out()
feature_names = np.concatenate([num_features, cat_features])

# ======================================================
# 5. COMPUTE SHAP VALUES
# ======================================================
print("🔹 Computing SHAP values (TreeExplainer)...")
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_t)

# ======================================================
# 6. SAVE SHAP PLOTS
# ======================================================
print("📈 Generating SHAP summary plots...")
plt.figure()
shap.summary_plot(shap_values, X_t, feature_names=feature_names, show=False)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "shap_values_summary.png"), dpi=250)
plt.close()

plt.figure()
shap.summary_plot(shap_values, X_t, feature_names=feature_names, plot_type="bar", show=False, max_display=TOP_N)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "shap_summary_bar.png"), dpi=250)
plt.close()

# ======================================================
# 7. SAVE TOP FEATURES
# ======================================================
abs_mean_shap = np.abs(shap_values).mean(axis=0)
top_idx = np.argsort(abs_mean_shap)[::-1][:TOP_N]
top_features = pd.DataFrame({
    "feature": feature_names[top_idx],
    "mean_abs_shap": abs_mean_shap[top_idx]
})
top_features.to_csv(os.path.join(OUTPUT_DIR, "shap_top_features.csv"), index=False)
print("✅ Top SHAP features saved to shap_top_features.csv")

# ======================================================
# 8. OPTIONAL: INDIVIDUAL FORCE PLOT
# ======================================================
try:
    idx = np.argmax(y)  # one severe CRS patient
    shap.initjs()
    force_plot = shap.force_plot(explainer.expected_value, shap_values[idx, :], feature_names=feature_names)
    shap.save_html(os.path.join(OUTPUT_DIR, "force_plot_example.html"), force_plot)
    print("✅ Individual force plot saved: force_plot_example.html")
except Exception as e:
    print(f"⚠️ Force plot skipped: {e}")

print(f"\n🎉 SHAP interpretation complete. Results in {OUTPUT_DIR}")