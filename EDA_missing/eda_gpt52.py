#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clinical Missingness Analysis — Enhanced & Scalable (Static + Dynamic)
--------------------------------------------------------------------
Updated to address large-cohort visualization and scalability concerns.

What changed (high level):
- Removed reliance on patient ID labels on axes for large datasets.
- Use summary / aggregate visualizations for dynamic data when dataset is large (> SMALL_N_THRESHOLD).
  * Per-patient availability distribution: histogram (shows how many patients have high/low data completeness).
  * Per-day trend: median availability across patients with IQR shading (shows temporal trends across -15..+30 days).
  * Boxplots for clinical phases (pre / day0 / post) to compare distributions concisely.
  * Variable-level missingness histograms per dynamic group (to inspect within-group spread).
- For small datasets (<= SMALL_N_THRESHOLD), an optional per-patient heatmap (without verbose ID ticks) is available.
- Fully modular functions and rich inline comments explaining every major step.
- Command-line interface (argparse) so you can customize paths and thresholds easily.

Usage (examples):
1) Default run (uses built-in paths):
   python clinical_missingness_enhanced.py

2) Specify custom folders and output path:
   python clinical_missingness_enhanced.py \
       --static /path/to/encoded.csv \
       --dynamic /path/to/processed/ \
       --out ./figures --small-threshold 60

3) Force per-patient heatmap even for larger cohorts (not recommended):
   python clinical_missingness_enhanced.py --force-heatmap

Output:
- PNG files in the output folder (default ./figures):
  * static_missingness.png
  * dynamic_group_missingness.png
  * dynamic_per_patient_availability_hist.png
  * dynamic_per_day_trend.png
  * dynamic_phase_boxplot.png
  * dynamic_group_var_missing_hist_<group>.png (one per group)
  * (optional) dynamic_availability_heatmap.png (only for small cohorts or when forced)
- CSV summary tables in ./figures/tables/

Notes on assumptions:
- Dynamic CSVs share the same set of columns and day indices (we align with the first file's header and day index).
- All dynamic values are numeric or NA; we coerce to numeric where appropriate.

"""

import argparse
import glob
import os
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------- Configuration defaults ---------------------------
DEFAULT_STATIC = Path("/home/phl/PHL/pytorch-forecasting/datasetcart/encoded.csv")
DEFAULT_DYNAMIC_DIR = Path("/home/phl/PHL/pytorch-forecasting/datasetcart/processed")
DEFAULT_OUT = Path("./figures")
DEFAULT_SMALL_THRESHOLD = 50  # <=50 considered 'small' -> may show per-patient heatmap

plt.rcParams.update({
    "figure.dpi": 140,
    "savefig.dpi": 300,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
})

# --------------------------- Utilities ---------------------------

def list_dynamic_csvs(dynamic_dir: Path) -> List[Path]:
    """Return a sorted list of CSV files in dynamic_dir.

    Sort numerically when file stems are integers (1.csv, 2.csv, ...), else lexicographically.
    """
    files = [Path(p) for p in glob.glob(str(dynamic_dir / "*.csv"))]

    def key(p: Path):
        try:
            return int(p.stem)
        except Exception:
            return p.stem

    return sorted(files, key=key)


def percent(numer: float, denom: float) -> float:
    return (float(numer) / float(denom) * 100.0) if denom else 0.0


def human_group_label(prefix3: str) -> str:
    mapping = {
        "CBC": "CBC",
        "Inf": "Inflammatory Biomarkers",
        "VCN": "VCN",
        "Lym": "Lymphocyte Subsets",
        "Coa": "Coagulation",
        "Ele": "Electrolytes",
        "Bio": "Biochemistry",
        "Vit": "Vital Signs",
    }
    return mapping.get(prefix3, prefix3)

# --------------------------- Static data functions ---------------------------

def load_static_matrix(static_path: Path) -> pd.DataFrame:
    """Load static encoded.csv into DataFrame with rows=variables, cols=patient IDs.

    The file is expected to have the first column as variable names (index) and
    subsequent columns are patient values.
    """
    df = pd.read_csv(static_path, header=0, index_col=0)
    # Coerce to numeric where possible (keep NA)
    df = df.apply(pd.to_numeric, errors='coerce')
    return df


def analyze_static_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame summarizing missingness per static variable.

    Columns: variable, missing_count, total, missing_pct, ratio
    """
    total_patients = df.shape[1]
    miss_count = df.isna().sum(axis=1)
    res = pd.DataFrame({
        "variable": df.index,
        "missing_count": miss_count.values,
        "total": total_patients,
    })
    res["missing_pct"] = res.apply(lambda r: percent(r["missing_count"], r["total"]), axis=1)
    res["ratio"] = res.apply(lambda r: f"{int(r['missing_count'])}/{int(r['total'])}", axis=1)
    res = res.sort_values("missing_pct", ascending=False, kind="mergesort").reset_index(drop=True)
    return res


def plot_static_missingness(summary: pd.DataFrame, out_dir: Path):
    """Plot static missingness: left bar chart, right table (saved to out_dir)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [3, 2]})

    # Bar chart
    x = np.arange(len(summary))
    bars = axes[0].bar(x, summary["missing_pct"].values)
    axes[0].set_title("Static Variables: Missing Data (%)")
    axes[0].set_ylabel("Missing (%)")
    axes[0].set_xlabel("Variables")

    # X ticks: show all labels if reasonable
    if len(summary) <= 50:
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(summary["variable"].tolist(), rotation=75, ha='right')
    else:
        # reduce labels to avoid clutter
        step = max(1, len(summary) // 40)
        idx = np.arange(0, len(summary), step)
        axes[0].set_xticks(idx)
        axes[0].set_xticklabels(summary["variable"].iloc[idx].tolist(), rotation=75, ha='right')

    axes[0].grid(axis='y', linestyle='--', alpha=0.4)

    # Table
    table_df = summary[["variable", "missing_pct", "ratio"]].copy()
    table_df["missing_pct"] = table_df["missing_pct"].map(lambda x: f"{x:.2f}%")
    axes[1].axis('off')
    axes[1].set_title("Static Variables — Missingness Table")
    tbl = axes[1].table(cellText=table_df.values, colLabels=table_df.columns, loc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.2)

    fig.tight_layout()
    p = out_dir / "static_missingness.png"
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)
    print(f"[Saved] {p}")

    # Save CSV summary
    table_dir = out_dir / "tables"
    table_dir.mkdir(exist_ok=True)
    table_csv = table_dir / "static_missingness_summary.csv"
    summary.to_csv(table_csv, index=False)
    print(f"[Saved] {table_csv}")

# --------------------------- Dynamic data functions ---------------------------

def load_first_dynamic_header(dynamic_dir: Path) -> Tuple[List[str], np.ndarray]:
    """Read the header (variable columns) and day index from the first file.

    Returns (columns_list, day_index_array)
    """
    files = list_dynamic_csvs(dynamic_dir)
    if not files:
        raise FileNotFoundError(f"No CSV files found in {dynamic_dir}")
    first = files[0]
    df0 = pd.read_csv(first, header=0, index_col=0)
    # Day index
    day_idx = df0.index.to_series().astype(float).values
    # Column names (skip first column which is day index)
    cols = df0.columns.tolist()
    return cols, day_idx


def build_dynamic_groups(columns: List[str]) -> Dict[str, List[str]]:
    """Group dynamic columns by their first three characters."""
    groups: Dict[str, List[str]] = {}
    for c in columns:
        code = str(c)[:3]
        groups.setdefault(code, []).append(c)
    return groups


def analyze_dynamic_group_missingness(dynamic_dir: Path, groups: Dict[str, List[str]]) -> pd.DataFrame:
    """Compute missing cells and variable-level missingness for each group across all patients and days."""
    files = list_dynamic_csvs(dynamic_dir)
    if not files:
        raise FileNotFoundError(f"No CSV files found in {dynamic_dir}")

    # Initialize accumulators
    group_missing_cells = {g: 0 for g in groups}
    group_total_cells = {g: 0 for g in groups}
    var_any_missing = {v: False for cols in groups.values() for v in cols}

    # We'll align to the first file's columns and days (assumption: consistent format)
    first_df = pd.read_csv(files[0], header=0, index_col=0)
    day_index = first_df.index.astype(float).sort_values().values
    keep_cols = [v for cols in groups.values() for v in cols]

    for fp in files:
        df = pd.read_csv(fp, header=0, index_col=0)
        df.index = pd.to_numeric(df.index, errors='coerce')
        df = df.sort_index()
        df = df.reindex(index=day_index, columns=keep_cols)
        # Coerce to numeric
        df = df.apply(pd.to_numeric, errors='coerce')

        # Group-level
        for g, cols in groups.items():
            sub = df[cols]
            miss = int(sub.isna().sum().sum())
            tot = sub.size
            group_missing_cells[g] += miss
            group_total_cells[g] += tot

        # Variable-level any-missing
        var_na = df.isna().any(axis=0)
        for v, any_na in var_na.items():
            if any_na:
                var_any_missing[v] = True

    rows = []
    for g, cols in groups.items():
        mc = group_missing_cells[g]
        tc = group_total_cells[g]
        pct = percent(mc, tc)
        vars_total = len(cols)
        vars_missing_any = sum(1 for v in cols if var_any_missing.get(v, False))
        rows.append({
            "group_code": g,
            "group_label": human_group_label(g),
            "missing_cells": mc,
            "total_cells": tc,
            "missing_pct": pct,
            "variables_with_any_missing": vars_missing_any,
            "variables_total": vars_total,
            "var_missing_ratio": f"{vars_missing_any}/{vars_total}",
        })

    df_summary = pd.DataFrame(rows).sort_values("missing_pct", ascending=False, kind="mergesort").reset_index(drop=True)
    return df_summary


def compute_availability_matrices(dynamic_dir: Path, groups: Dict[str, List[str]]) -> Tuple[np.ndarray, List[str], np.ndarray]:
    """Compute availability matrices and per-patient/per-day aggregates.

    Returns: (avail_matrix, patient_ids, day_index)
      - avail_matrix: shape (n_patients, n_days) where each cell is fraction non-NA across all kept variables
      - patient_ids: list of patient file stems in same order
      - day_index: 1D numpy array of day indices
    """
    files = list_dynamic_csvs(dynamic_dir)
    if not files:
        return np.zeros((0, 0)), [], np.array([])

    first_df = pd.read_csv(files[0], header=0, index_col=0)
    day_index = first_df.index.astype(float).sort_values().values
    keep_cols = [v for cols in groups.values() for v in cols]

    avail_rows = []
    patient_ids = []

    for fp in files:
        df = pd.read_csv(fp, header=0, index_col=0)
        df.index = pd.to_numeric(df.index, errors='coerce')
        df = df.sort_index()
        # Align to master day_index and columns
        df = df.reindex(index=day_index, columns=keep_cols)
        df = df.apply(pd.to_numeric, errors='coerce')

        # For each day, fraction of non-na across variables
        avail_frac = (1.0 - df.isna().mean(axis=1)).values.astype(float)  # len = n_days
        avail_rows.append(avail_frac)
        patient_ids.append(fp.stem)

    avail_mat = np.vstack(avail_rows) if avail_rows else np.zeros((0, len(day_index)))
    return avail_mat, patient_ids, day_index

# --------------------------- Dynamic plotting (scalable) ---------------------------

def plot_dynamic_group_summary(group_summary: pd.DataFrame, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={"width_ratios": [3, 2]})

    # Left: group-level missing % bar chart
    x = np.arange(len(group_summary))
    bars = axes[0].bar(x, group_summary["missing_pct"].values)
    axes[0].set_title("Dynamic Groups: Missing Data (%)")
    axes[0].set_ylabel("Missing (%)")
    axes[0].set_xlabel("Group")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([f"{lbl}({code})" for lbl, code in zip(group_summary["group_label"], group_summary["group_code"])], rotation=0)
    axes[0].grid(axis='y', linestyle='--', alpha=0.4)

    # Right: table
    table_df = group_summary[["group_label", "missing_pct", "var_missing_ratio"]].copy()
    table_df.rename(columns={"group_label": "Group", "missing_pct": "Missing %", "var_missing_ratio": "Vars Missing (any)"}, inplace=True)
    table_df["Missing %"] = table_df["Missing %"].map(lambda x: f"{x:.2f}%")
    axes[1].axis('off')
    axes[1].set_title("Dynamic Groups — Missingness Table")
    tbl = axes[1].table(cellText=table_df.values, colLabels=table_df.columns, loc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.2)

    fig.tight_layout()
    p = out_dir / "dynamic_group_missingness.png"
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)
    print(f"[Saved] {p}")

    # Save CSV
    (out_dir / "tables").mkdir(exist_ok=True)
    group_summary.to_csv(out_dir / "tables" / "dynamic_group_missingness_summary.csv", index=False)


def plot_per_patient_availability_hist(avail_mat: np.ndarray, out_dir: Path):
    """Histogram of per-patient average availability across days (one value per patient).

    This is a compact way to assess cohort-level completeness without plotting each patient.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if avail_mat.size == 0:
        print("[WARN] Empty availability matrix; skipping per-patient histogram.")
        return

    per_patient_mean = np.nanmean(avail_mat, axis=1)  # mean across days for each patient

    fig, ax = plt.subplots(1, 1, figsize=(8, 4))
    ax.hist(per_patient_mean, bins=30, edgecolor='k')
    ax.set_title("Per-patient Availability Distribution")
    ax.set_xlabel("Average availability (fraction non-NA)")
    ax.set_ylabel("Number of patients")
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    # Annotate mean
    mean_val = np.nanmean(per_patient_mean)
    ax.axvline(mean_val, linestyle='--')
    ax.annotate(f"mean={mean_val:.2f}", xy=(mean_val, ax.get_ylim()[1]*0.9), rotation=90)

    p = out_dir / "dynamic_per_patient_availability_hist.png"
    fig.tight_layout()
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)
    print(f"[Saved] {p}")


def plot_per_day_trend(avail_mat: np.ndarray, day_index: np.ndarray, out_dir: Path):
    """Plot median availability per day with IQR shading.

    This is a compact trend that summarizes temporal completeness across the cohort.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if avail_mat.size == 0:
        print("[WARN] Empty availability matrix; skipping per-day trend.")
        return

    # avail_mat shape: (n_patients, n_days)
    median = np.nanmedian(avail_mat, axis=0)
    p25 = np.nanpercentile(avail_mat, 25, axis=0)
    p75 = np.nanpercentile(avail_mat, 75, axis=0)

    fig, ax = plt.subplots(1, 1, figsize=(10, 4))
    ax.plot(day_index, median, label='median')
    ax.fill_between(day_index, p25, p75, alpha=0.3, label='IQR (25-75%)')
    ax.set_title("Per-day Availability Trend (median & IQR)")
    ax.set_xlabel("Day")
    ax.set_ylabel("Availability (fraction non-NA)")
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.legend()

    p = out_dir / "dynamic_per_day_trend.png"
    fig.tight_layout()
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)
    print(f"[Saved] {p}")


def plot_phase_boxplots(avail_mat: np.ndarray, day_index: np.ndarray, out_dir: Path):
    """Create boxplots for pre / day0 / post phases to compare distributions compactly.

    Phase definitions (by day index values):
      - pre: day < 0
      - day0: day == 0 (if present)
      - post: day > 0

    If a phase has no days (e.g., no day0), it will be skipped.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if avail_mat.size == 0:
        print("[WARN] Empty availability matrix; skipping phase boxplots.")
        return

    pre_idx = np.where(day_index < 0)[0]
    day0_idx = np.where(day_index == 0)[0]
    post_idx = np.where(day_index > 0)[0]

    data = []
    labels = []
    if len(pre_idx) > 0:
        data.append(avail_mat[:, pre_idx].mean(axis=1))
        labels.append('pre (<0)')
    if len(day0_idx) > 0:
        data.append(avail_mat[:, day0_idx].mean(axis=1))
        labels.append('day0 (0)')
    if len(post_idx) > 0:
        data.append(avail_mat[:, post_idx].mean(axis=1))
        labels.append('post (>0)')

    if not data:
        print("[WARN] No phase days found; skipping phase boxplots.")
        return

    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    ax.boxplot(data, labels=labels, showfliers=False)
    ax.set_title("Per-patient Availability by Clinical Phase (mean per phase)")
    ax.set_ylabel("Average availability (fraction non-NA)")
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    p = out_dir / "dynamic_phase_boxplot.png"
    fig.tight_layout()
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)
    print(f"[Saved] {p}")


def plot_group_variable_missing_histograms(dynamic_dir: Path, groups: Dict[str, List[str]], out_dir: Path):
    """For each dynamic group, compute variable-wise missing % (across all patients & days) and plot a histogram.

    This helps to see whether missingness is concentrated in a few variables or spread.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    files = list_dynamic_csvs(dynamic_dir)
    if not files:
        print("[WARN] No dynamic files; skipping group-variable histograms.")
        return

    # Align to first file columns & days
    first_df = pd.read_csv(files[0], header=0, index_col=0)
    day_index = first_df.index.astype(float).sort_values().values
    keep_cols = [v for cols in groups.values() for v in cols]

    # We'll compute missing% per variable across all patients+days
    var_missing_total = {v: 0 for v in keep_cols}
    var_total_cells = {v: 0 for v in keep_cols}

    for fp in files:
        df = pd.read_csv(fp, header=0, index_col=0)
        df.index = pd.to_numeric(df.index, errors='coerce')
        df = df.sort_index()
        df = df.reindex(index=day_index, columns=keep_cols)
        df = df.apply(pd.to_numeric, errors='coerce')

        for v in keep_cols:
            col = df[v]
            var_missing_total[v] += int(col.isna().sum())
            var_total_cells[v] += col.size

    # Build per-group histograms
    for g, cols in groups.items():
        miss_pcts = [percent(var_missing_total[v], var_total_cells[v]) if var_total_cells[v] else 0.0 for v in cols]
        if not miss_pcts:
            continue
        fig, ax = plt.subplots(1, 1, figsize=(7, 4))
        ax.hist(miss_pcts, bins=20, edgecolor='k')
        ax.set_title(f"Variable-level Missingness Distribution — {human_group_label(g)}")
        ax.set_xlabel("Missing % per variable")
        ax.set_ylabel("Number of variables")
        ax.grid(axis='y', linestyle='--', alpha=0.4)

        p = out_dir / f"dynamic_group_var_missing_hist_{g}.png"
        fig.tight_layout()
        fig.savefig(p, bbox_inches='tight')
        plt.close(fig)
        print(f"[Saved] {p}")


def optional_heatmap_for_small_cohorts(avail_mat: np.ndarray, out_dir: Path, patient_ids: List[str], day_index: np.ndarray, force_heatmap: bool = False, small_threshold: int = 50):
    """Show a compact heatmap only for small cohorts or when forced.

    - To keep the plot readable we do NOT print all patient IDs when cohort is large.
    - When cohort size <= small_threshold we label a subset of patient ticks; otherwise no patient tick labels.
    """
    if avail_mat.size == 0:
        print("[WARN] Empty availability matrix; skipping heatmap.")
        return

    n_patients = avail_mat.shape[0]
    if (n_patients > small_threshold) and not force_heatmap:
        print("[INFO] Cohort too large for per-patient heatmap; skipped. Use --force-heatmap to override.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(min(14, 4 + avail_mat.shape[1]*0.15), min(8, 2 + avail_mat.shape[0]*0.06)))

    im = ax.imshow(avail_mat, aspect='auto', interpolation='nearest', origin='upper', cmap='viridis', vmin=0, vmax=1)
    ax.set_title("Dynamic Data Availability (patients × days)")
    ax.set_xlabel("Day")
    ax.set_ylabel("Patient (index order)")

    # X tick labels (days): show a reasonable subset
    n_days = len(day_index)
    if n_days <= 20:
        ax.set_xticks(np.arange(n_days))
        ax.set_xticklabels([str(int(d)) for d in day_index], rotation=0)
    else:
        step = max(1, n_days // 12)
        idx = np.arange(0, n_days, step)
        ax.set_xticks(idx)
        ax.set_xticklabels([str(int(day_index[i])) for i in idx], rotation=0)

    # Y tick labels: only label a few or none
    if n_patients <= 30:
        ax.set_yticks(np.arange(n_patients))
        ax.set_yticklabels(patient_ids)
    else:
        # show only few numeric labels (row indices)
        step = max(1, n_patients // 10)
        idx = np.arange(0, n_patients, step)
        ax.set_yticks(idx)
        ax.set_yticklabels([str(i) for i in idx])

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Availability (fraction non-NA)")

    p = out_dir / "dynamic_availability_heatmap.png"
    fig.tight_layout()
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)
    print(f"[Saved] {p}")

# --------------------------- Orchestrator / CLI ---------------------------

def main(static_path: Path, dynamic_dir: Path, out_dir: Path, small_threshold: int, force_heatmap: bool):
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------- Static ----------
    if not static_path.exists():
        print(f"[WARN] Static file not found: {static_path} (skipping static analysis)")
    else:
        print("[Info] Loading static data...")
        static_df = load_static_matrix(static_path)
        print(f"[Info] Static matrix shape: {static_df.shape} (variables x patients)")
        static_summary = analyze_static_missingness(static_df)
        plot_static_missingness(static_summary, out_dir)

    # ---------- Dynamic: header and groups ----------
    if not dynamic_dir.exists():
        print(f"[WARN] Dynamic folder not found: {dynamic_dir} (skipping dynamic analysis)")
        return

    print("[Info] Loading dynamic header and building groups...")
    dyn_cols, day_index = load_first_dynamic_header(dynamic_dir)
    groups = build_dynamic_groups(dyn_cols)
    print(f"[Info] Detected groups: {', '.join([human_group_label(g)+f'({g})' for g in groups.keys()])}")

    print("[Info] Computing group-level missingness summary...")
    group_summary = analyze_dynamic_group_missingness(dynamic_dir, groups)
    plot_dynamic_group_summary(group_summary, out_dir)

    # Availability matrix and derived summaries
    print("[Info] Computing availability matrix (this loads all dynamic CSVs) -- memory is moderate for ~500x45 cells")
    avail_mat, patient_ids, day_index = compute_availability_matrices(dynamic_dir, groups)
    n_patients = avail_mat.shape[0]
    n_days = avail_mat.shape[1] if avail_mat.size else 0
    print(f"[Info] Processed {n_patients} patient files; days per file = {n_days}")

    # Scalable visualizations (summary-first approach)
    plot_per_patient_availability_hist(avail_mat, out_dir)
    plot_per_day_trend(avail_mat, day_index, out_dir)
    plot_phase_boxplots(avail_mat, day_index, out_dir)
    plot_group_variable_missing_histograms(dynamic_dir, groups, out_dir)

    # Optional per-patient heatmap only for small cohorts or when forced
    optional_heatmap_for_small_cohorts(avail_mat, out_dir, patient_ids, day_index, force_heatmap=force_heatmap, small_threshold=small_threshold)

    print("[Done] All requested visualizations saved to:", out_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scalable clinical missingness analysis (static + dynamic)')
    parser.add_argument('--static', type=Path, default=DEFAULT_STATIC, help='Path to static encoded.csv')
    parser.add_argument('--dynamic', type=Path, default=DEFAULT_DYNAMIC_DIR, help='Path to dynamic processed folder')
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT, help='Output folder for figures and tables')
    parser.add_argument('--small-threshold', type=int, default=DEFAULT_SMALL_THRESHOLD, help='Max cohort size to show per-patient heatmap')
    parser.add_argument('--force-heatmap', action='store_true', help='Force generation of per-patient heatmap even if cohort is large')
    args = parser.parse_args()

    main(args.static, args.dynamic, args.out, args.small_threshold, args.force_heatmap)
