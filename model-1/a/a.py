"""
Pipeline template: observation window Day -15..+2 -> predict Day +3..+5 severe CRS (>=3)
Requirements: pandas, numpy, sklearn, lightgbm, scipy, joblib
"""

import os
import glob
import numpy as np
import pandas as pd
from scipy import stats
from scipy.integrate import trapezoid
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GroupKFold
from sklearn.metrics import (
    roc_auc_score, average_precision_score, precision_recall_curve,
    roc_curve, precision_score, recall_score, f1_score, brier_score_loss
)
from lightgbm import LGBMClassifier
import joblib
from collections import defaultdict
from typing import List, Dict

# ---------------------------
# Paths & settings (customize)
# ---------------------------
STATIC_CSV = "/home/phl/PHL/Car-T/data_encoder/output/dataset/encoded_standardized.csv"
DYNAMIC_DIR = "/home/phl/PHL/pytorch-forecasting/datasetcart/processed"  # files named "1.csv", "2.csv" ...
CRS_COL_IN_STATIC = "CRS_grade"  # if static file contains CRS grades per patient (useful for label creation)
PATIENT_ID_COL = "patient_id"  # in static.csv
OBS_START, OBS_END = -15, 2    # inclusive observation window
LABEL_START, LABEL_END = 3, 5   # inclusive prediction window
N_SPLITS = 5
RANDOM_STATE = 42

# ---------------------------
# UTILITIES: dynamic aggregation
# ---------------------------

def aggregate_time_series(df_ts: pd.DataFrame, obs_start=-15, obs_end=2):
    """
    Input:
        df_ts: DataFrame with first column 'Day' (int -15..+30) and rest measurement columns (float/NA)
    Output:
        dict of aggregated features for this patient within [obs_start, obs_end]
    For each timeseries column X:
        - X_mean, X_median, X_std, X_min, X_max
        - X_slope (linear regression over available points, nan if <2 points)
        - X_auc (trapezoid area relative to days; nan if <2 points)
        - X_time_to_peak (day index relative to day 0 where max occurs, nan if no values)
        - X_nonmiss_count, X_last_value (value at obs_end if exists or last available)
    Missing handling: return np.nan; later pipeline provides missing indicators/imputation.
    """
    features = {}
    # ensure Day column named 'Day' and numeric
    if 'Day' not in df_ts.columns and df_ts.columns[0].lower() == 'day':
        df_ts = df_ts.rename(columns={df_ts.columns[0]: 'Day'})
    if 'Day' not in df_ts.columns:
        raise ValueError("time series file must have a 'Day' column")

    # filter observation window
    df = df_ts[(df_ts['Day'] >= obs_start) & (df_ts['Day'] <= obs_end)].copy()
    days = df['Day'].values
    if len(df) == 0:
        # return empty features with NaNs
        return features

    ts_cols = [c for c in df.columns if c != 'Day']
    for col in ts_cols:
        series = df[[ 'Day', col ]].dropna(subset=[col])
        vals = series[col].values
        ds = series['Day'].values
        prefix = col
        # counts and basic stats
        features[f"{prefix}_count"] = len(vals)
        if len(vals) == 0:
            # fill placeholders
            features.update({
                f"{prefix}_mean": np.nan,
                f"{prefix}_median": np.nan,
                f"{prefix}_std": np.nan,
                f"{prefix}_min": np.nan,
                f"{prefix}_max": np.nan,
                f"{prefix}_slope": np.nan,
                f"{prefix}_auc": np.nan,
                f"{prefix}_time_to_peak": np.nan,
                f"{prefix}_last_value": np.nan,
            })
            continue

        features[f"{prefix}_mean"] = np.nanmean(vals)
        features[f"{prefix}_median"] = np.nanmedian(vals)
        features[f"{prefix}_std"] = np.nanstd(vals, ddof=0)
        features[f"{prefix}_min"] = np.nanmin(vals)
        features[f"{prefix}_max"] = np.nanmax(vals)

        # slope: linear regression of val ~ day
        if len(vals) >= 2 and len(np.unique(ds)) >= 2:
            slope, intercept, r_value, p_value, std_err = stats.linregress(ds, vals)
            features[f"{prefix}_slope"] = slope
        else:
            features[f"{prefix}_slope"] = np.nan

        # auc (area under curve)
        if len(vals) >= 2:
            try:
                features[f"{prefix}_auc"] = trapezoid(vals, ds)
            except Exception:
                features[f"{prefix}_auc"] = np.nan
        else:
            features[f"{prefix}_auc"] = np.nan

        # time to peak (relative to day 0)
        idx_max = np.argmax(vals)
        features[f"{prefix}_time_to_peak"] = float(ds[idx_max])  # day index
        # last value before/at obs_end
        # get value at obs_end if present, else last available
        last_idx = np.where(ds <= obs_end)[0]
        if len(last_idx) > 0:
            last_val = vals[last_idx[-1]]
            features[f"{prefix}_last_value"] = float(last_val)
        else:
            features[f"{prefix}_last_value"] = np.nan

    # also add measurement frequency meta-features for this patient
    # e.g., total non-missing measurements across all vars, proportion of days with any measurement
    df_nonmiss = df.drop(columns=['Day']).notna()
    features['total_nonmiss_measurements'] = int(df_nonmiss.values.sum())
    days_with_any = (df_nonmiss.sum(axis=1) > 0).sum()
    features['days_with_any_measurements'] = int(days_with_any)

    return features


# ---------------------------
# Load static table & build labels
# ---------------------------

def load_static_table(static_csv: str):
    df = pd.read_csv(static_csv)
    # ensure patient id column present
    if PATIENT_ID_COL not in df.columns:
        # try common alternatives:
        alt = [c for c in df.columns if 'id' in c.lower()]
        if alt:
            df = df.rename(columns={alt[0]: PATIENT_ID_COL})
        else:
            raise ValueError("patient id column not found in static CSV")
    return df

def label_from_static_or_dynamic(static_df: pd.DataFrame, dynamic_dir: str, patient_id_col=PATIENT_ID_COL,
                                 label_start=3, label_end=5):
    """
    Build binary label: 1 if within Day label_start..label_end patient has CRS >=3.
    If static table already contains per-patient CRS time series or max grade, you can adapt this.
    Here we attempt to find per-patient dynamic file or use static CRS grade column if available.
    """
    labels = {}
    for _, row in static_df.iterrows():
        pid = int(row[patient_id_col])
        fname = os.path.join(dynamic_dir, f"{pid}.csv")
        lab = 0
        if os.path.exists(fname):
            dft = pd.read_csv(fname)
            # assume there is a column "CRS_grade" or similar (if not, you must adapt)
            # If CRS labels are not in dynamic files, attempt to use a static field 'CRS_max_day'
            if 'CRS_grade' in dft.columns:
                dflab = dft[(dft['Day'] >= label_start) & (dft['Day'] <= label_end)]
                if len(dflab) > 0 and (dflab['CRS_grade'].fillna(0) >= 3).any():
                    lab = 1
            else:
                # fallback: check if static contains label or max grade
                if 'CRS_max_overall' in row.index and not pd.isna(row['CRS_max_overall']):
                    lab = int(row['CRS_max_overall'] >= 3)
                elif 'CRS_grade' in row.index and not pd.isna(row['CRS_grade']):
                    # assume static CRS_grade is overall or max
                    lab = int(row['CRS_grade'] >= 3)
                else:
                    # default 0 (you may want to flag these)
                    lab = 0
        else:
            # no dynamic file: try static
            if 'CRS_max_overall' in row.index and not pd.isna(row['CRS_max_overall']):
                lab = int(row['CRS_max_overall'] >= 3)
            elif 'CRS_grade' in row.index and not pd.isna(row['CRS_grade']):
                lab = int(row['CRS_grade'] >= 3)
            else:
                lab = 0
        labels[pid] = lab
    return labels


# ---------------------------
# Full feature assembly across patients
# ---------------------------

def build_dataset(static_csv: str, dynamic_dir: str,
                  obs_start=-15, obs_end=2, label_start=3, label_end=5) -> pd.DataFrame:
    static_df = load_static_table(static_csv)
    labels = label_from_static_or_dynamic(static_df, dynamic_dir, label_start=label_start, label_end=label_end)
    features_list = []
    missing_dynamic_pids = []
    for _, row in static_df.iterrows():
        pid = int(row[PATIENT_ID_COL])
        fname = os.path.join(dynamic_dir, f"{pid}.csv")
        dyn_feats = {}
        if os.path.exists(fname):
            try:
                df_ts = pd.read_csv(fname)
                if 'Day' not in df_ts.columns and df_ts.columns[0].lower() == 'day':
                    df_ts = df_ts.rename(columns={df_ts.columns[0]: 'Day'})
                # ensure Day numeric
                df_ts['Day'] = pd.to_numeric(df_ts['Day'], errors='coerce')
                dyn_feats = aggregate_time_series(df_ts, obs_start, obs_end)
            except Exception as e:
                print(f"Warning: failed to process dynamic file {fname}: {e}")
                missing_dynamic_pids.append(pid)
                dyn_feats = {}
        else:
            missing_dynamic_pids.append(pid)
            dyn_feats = {}

        # flatten static row into features (prefix 's_')
        s_feats = {}
        for c in row.index:
            if c == PATIENT_ID_COL:
                continue
            s_feats[f"s_{c}"] = row[c]

        # label
        lab = labels.get(pid, 0)

        rec = {'patient_id': pid, 'label': lab}
        rec.update(s_feats)
        rec.update(dyn_feats)
        features_list.append(rec)

    df_all = pd.DataFrame(features_list)
    # Optionally: save df_all to disk
    return df_all

# ---------------------------
# Preprocessing and modeling within CV loops (avoid leakage)
# ---------------------------

def run_group_cv(df_all: pd.DataFrame,
                 id_col='patient_id',
                 label_col='label',
                 n_splits=5,
                 random_state=RANDOM_STATE):
    # identify columns
    all_cols = [c for c in df_all.columns if c not in [id_col, label_col]]
    # identify numeric vs categorical (static categorical have 's_' prefix and are object dtype)
    numeric_cols = df_all[all_cols].select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [c for c in all_cols if c not in numeric_cols]

    # Build preprocessing pipelines
    numeric_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),  # fit on train only inside loop
        ('scaler', StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse=False))
    ])
    preprocessor = ColumnTransformer([
        ('num', numeric_pipeline, numeric_cols),
        ('cat', categorical_pipeline, categorical_cols)
    ], remainder='drop')

    # Model (LightGBM)
    lgb = LGBMClassifier(
        n_estimators=1000,
        objective='binary',
        boosting_type='gbdt',
        metric='None',
        random_state=random_state,
        n_jobs=4,
        # scale_pos_weight will be set per-train fold based on class balance
    )

    # CV: GroupKFold to ensure patient-level split (here groups are patient ids)
    groups = df_all[id_col].values
    labels = df_all[label_col].values
    gkf = GroupKFold(n_splits=n_splits)

    # store OOF preds
    oof_preds = np.zeros(len(df_all))
    oof_probs = np.zeros(len(df_all))
    fold_metrics = []
    fold_idx = 0
    for train_idx, test_idx in gkf.split(df_all, labels, groups=groups):
        fold_idx += 1
        X_train = df_all.iloc[train_idx].drop([id_col, label_col], axis=1)
        y_train = df_all.iloc[train_idx][label_col].values
        X_test = df_all.iloc[test_idx].drop([id_col, label_col], axis=1)
        y_test = df_all.iloc[test_idx][label_col].values

        # adjusting class weight
        pos = y_train.sum()
        neg = len(y_train) - pos
        if pos == 0:
            print(f"Warning: fold {fold_idx} has zero positive samples.")
            scale_pos_weight = 1.0
        else:
            scale_pos_weight = neg / pos
        lgb.set_params(scale_pos_weight=scale_pos_weight)

        # fit preprocessor on train
        preprocessor.fit(X_train)
        X_train_trans = preprocessor.transform(X_train)
        X_test_trans = preprocessor.transform(X_test)

        # feature names for LightGBM (optional)
        # train model with early_stopping on a small validation split (internal)
        # create a small validation split from train to enable early stopping
        # here we do a simple holdout 80/20 from X_train
        n_train = X_train_trans.shape[0]
        val_split = int(n_train * 0.8)
        # shuffle
        idxs = np.arange(n_train)
        rng = np.random.RandomState(RANDOM_STATE + fold_idx)
        rng.shuffle(idxs)
        tr_idx = idxs[:val_split]
        val_idx = idxs[val_split:]
        X_tr, X_val = X_train_trans[tr_idx], X_train_trans[val_idx]
        y_tr, y_val = y_train[tr_idx], y_train[val_idx]

        lgb.fit(
            X_tr, y_tr,
            eval_set=[(X_val, y_val)],
            eval_metric='auc',
            early_stopping_rounds=50,
            verbose=False
        )

        # predict
        proba = lgb.predict_proba(X_test_trans)[:, 1]
        preds = (proba >= 0.5).astype(int)

        oof_preds[test_idx] = preds
        oof_probs[test_idx] = proba

        # fold metrics
        try:
            roc = roc_auc_score(y_test, proba)
        except ValueError:
            roc = np.nan
        try:
            pr = average_precision_score(y_test, proba)
        except ValueError:
            pr = np.nan
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        brier = brier_score_loss(y_test, proba)
        fold_metrics.append({
            'fold': fold_idx, 'roc_auc': roc, 'pr_auc': pr,
            'precision': prec, 'recall': rec, 'f1': f1, 'brier': brier,
            'num_train_pos': int(pos), 'num_train_neg': int(neg)
        })
        print(f"Fold {fold_idx} done: ROC {roc:.4f}, PR {pr:.4f}, F1 {f1:.3f}, Prec {prec:.3f}, Rec {rec:.3f}")

    # overall metrics
    overall = {}
    try:
        overall['roc_auc'] = roc_auc_score(labels, oof_probs)
        overall['pr_auc'] = average_precision_score(labels, oof_probs)
    except Exception:
        overall['roc_auc'] = np.nan
        overall['pr_auc'] = np.nan
    overall['precision'] = precision_score(labels, oof_preds, zero_division=0)
    overall['recall'] = recall_score(labels, oof_preds, zero_division=0)
    overall['f1'] = f1_score(labels, oof_preds, zero_division=0)
    overall['brier'] = brier_score_loss(labels, oof_probs)

    print("CV finished. Overall metrics:", overall)
    return {
        'preprocessor': preprocessor,
        'model': lgb,
        'oof_probs': oof_probs,
        'oof_preds': oof_preds,
        'fold_metrics': fold_metrics,
        'overall': overall
    }


# ---------------------------
# Example orchestration
# ---------------------------

def main():
    # 1) Build dataset (static + aggregated dynamic features)
    df_all = build_dataset(STATIC_CSV, DYNAMIC_DIR, OBS_START, OBS_END, LABEL_START, LABEL_END)
    print("Built dataset: rows:", len(df_all), "cols:", len(df_all.columns))
    # Optionally save
    df_all.to_csv("patient_feature_table.csv", index=False)

    # 2) Basic filters: remove patients with no dynamic data or all-nan features if desired
    # (but be careful: removing may bias sample)
    # Example: drop patients with total_nonmiss_measurements == 0
    if 'total_nonmiss_measurements' in df_all.columns:
        df_filtered = df_all[df_all['total_nonmiss_measurements'] > 0].reset_index(drop=True)
    else:
        df_filtered = df_all.copy()

    # 3) Run CV training & evaluation
    results = run_group_cv(df_filtered, id_col='patient_id', label_col='label', n_splits=N_SPLITS)

    # 4) Save preprocessor + model (fit on full data pipeline if desired)
    # Fit final pipeline on the whole dataset:
    X_full = df_filtered.drop(['patient_id', 'label'], axis=1)
    y_full = df_filtered['label'].values
    preproc = results['preprocessor']
    # Fit preprocessor on full
    preproc.fit(X_full)
    X_full_trans = preproc.transform(X_full)
    # train final model with balanced weight
    pos = y_full.sum(); neg = len(y_full) - pos
    final_model = LGBMClassifier(n_estimators=1000, random_state=RANDOM_STATE, n_jobs=4,
                                scale_pos_weight=(neg / max(pos, 1)))
    final_model.fit(X_full_trans, y_full, verbose=False)
    # Save
    joblib.dump({'preprocessor': preproc, 'model': final_model}, "pipeline_full_joblib.pkl")
    print("Saved final pipeline to pipeline_full_joblib.pkl")

if __name__ == "__main__":
    main()