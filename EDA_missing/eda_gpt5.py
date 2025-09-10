#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clinical Missingness Analysis (Static + Dynamic)
------------------------------------------------
This script reads static and dynamic clinical datasets and produces publication-grade
missingness analyses and visualizations, including:

1) Static data:
   - Left: bar chart of missing percentage per variable (across all patients)
   - Right: a data table with exact % and the missing ratio in "x/N" format

2) Dynamic data:
   - Uses ONLY the header row from the *first* dynamic CSV to define variable groups
     (all files share the same format)
   - Groups variables by the first three characters (e.g., CBC, Inf, VCN, Lym, Coa, Ele, Bio, Vit)
   - Left: bar chart of missing percentage per grouped category (across all patients and days)
   - Right: a data table with exact % and the ratio of variables-with-any-missing to total variables
   - Availability heatmap: shows per-patient per-day data availability (fraction of non-NA values)

Technical notes:
- Efficiently processes ~500 CSV files from the dynamic dataset
- Clear axis labels, consistent visual style, and robust NA handling
- Saves figures under ./figures

Paths (adjust if needed):
- Static:   /home/phl/PHL/pytorch-forecasting/datasetcart/encoded.csv
- Dynamic:  /home/phl/PHL/pytorch-forecasting/datasetcart/processed/
"""

import os
import sys
import glob
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
STATIC_PATH = Path("/home/phl/PHL/pytorch-forecasting/datasetcart/encoded.csv")
DYNAMIC_DIR = Path("/home/phl/PHL/pytorch-forecasting/datasetcart/processed")
FIG_DIR = Path("./output_gpt5")
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Figure aesthetics
plt.rcParams.update({
    "figure.dpi": 140,
    "savefig.dpi": 300,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
})

# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

def list_dynamic_csvs(dynamic_dir: Path) -> List[Path]:
    """Return a numerically sorted list of patient CSV paths in the processed folder."""
    files = [Path(p) for p in glob.glob(str(dynamic_dir / "*.csv"))]
    def patient_key(p: Path):
        # filenames are like "1.csv", "2.csv"; try to sort numerically by stem
        try:
            return int(p.stem)
        except ValueError:
            return p.stem
    return sorted(files, key=patient_key)


def human_group_label(prefix3: str) -> str:
    """Map 3-char group codes to readable labels."""
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


def compute_bar_positions(n: int) -> np.ndarray:
    return np.arange(n)


def percent(numer: float, denom: float) -> float:
    return (float(numer) / float(denom) * 100.0) if denom else 0.0


def annotate_bars_with_labels(ax: plt.Axes, bars, labels: List[str], pad: float = 0.5):
    """Annotate each bar top with a text label (e.g., "12.3% | 56/455")."""
    for rect, label in zip(bars, labels):
        height = rect.get_height()
        ax.annotate(label,
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, pad),
                    textcoords="offset points",
                    ha='center', va='bottom', rotation=90)

# ------------------------------------------------------------
# Static data processing
# ------------------------------------------------------------

def load_static_matrix(static_path: Path) -> pd.DataFrame:
    """
    Load the static encoded.csv.
    Assumed structure:
      - First row: header; first cell is a label (e.g., "病人索引ID号"), the rest are patient IDs.
      - First column: variable names; rows contain values per patient.
    Result: DataFrame indexed by variable (rows), columns are patient IDs.
    """
    df = pd.read_csv(static_path, header=0, index_col=0)
    # Ensure all non-index columns are treated as data (coerce to numeric when possible)
    df = df.apply(pd.to_numeric, errors='ignore')
    return df


def analyze_static_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute missingness per variable across all patients.
    Returns a DataFrame with columns: [variable, missing_count, total, missing_pct, ratio]
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
    # Sort descending by missing %
    res = res.sort_values("missing_pct", ascending=False, kind="mergesort").reset_index(drop=True)
    return res


def plot_static_missingness(summary: pd.DataFrame, max_labels: int = 50):
    """
    Create a 1x2 layout: (left) bar chart, (right) data table.
    If variables are many, only label top-N bars to keep figure readable (all bars still plotted).
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [3, 2]})

    # Left: bar chart
    x = compute_bar_positions(len(summary))
    bars = axes[0].bar(x, summary["missing_pct"].values)
    axes[0].set_title("Static Variables: Missing Data (%)")
    axes[0].set_ylabel("Missing (%)")
    axes[0].set_xlabel("Variables")

    # Manage x tick labels for readability
    if len(summary) <= max_labels:
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(summary["variable"].tolist(), rotation=75, ha='right')
        # Annotate each bar with "% | x/N"
        labels = [f"{v:.1f}% | {r}" for v, r in zip(summary["missing_pct"], summary["ratio"]) ]
        annotate_bars_with_labels(axes[0], bars, labels, pad=2)
    else:
        # Too many variables: lighter x-tick labeling
        step = max(1, len(summary)//max_labels)
        idx = np.arange(0, len(summary), step)
        axes[0].set_xticks(idx)
        axes[0].set_xticklabels(summary["variable"].iloc[idx].tolist(), rotation=75, ha='right')

    axes[0].grid(axis='y', linestyle='--', alpha=0.4)

    # Right: table with exact % and ratio
    table_df = summary[["variable", "missing_pct", "ratio"]].copy()
    table_df["missing_pct"] = table_df["missing_pct"].map(lambda x: f"{x:.2f}%")

    axes[1].axis('off')
    axes[1].set_title("Static Variables — Missingness Table")

    # Matplotlib table
    tbl = axes[1].table(cellText=table_df.values,
                        colLabels=table_df.columns,
                        loc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.2)

    fig.tight_layout()
    out_path = FIG_DIR / "static_missingness.png"
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f"[Saved] {out_path}")

# ------------------------------------------------------------
# Dynamic data processing
# ------------------------------------------------------------

def load_first_dynamic_header(dynamic_dir: Path) -> List[str]:
    """Read only the header row (and index col name) from the first dynamic CSV to define variable set."""
    files = list_dynamic_csvs(dynamic_dir)
    if not files:
        raise FileNotFoundError(f"No CSV files found in {dynamic_dir}")
    first = files[0]
    # Read header row
    df0 = pd.read_csv(first, nrows=0)
    cols = df0.columns.tolist()[1:]  # skip the first column (days index label)
    return cols


def build_dynamic_groups(columns: List[str]) -> Dict[str, List[str]]:
    """
    Group dynamic variable names by their first three characters.
    Returns dict: { group_code(3-char): [col1, col2, ...] }
    """
    groups: Dict[str, List[str]] = {}
    for c in columns:
        code = str(c)[:3]
        groups.setdefault(code, []).append(c)
    return groups


def analyze_dynamic_missingness(dynamic_dir: Path,
                                groups: Dict[str, List[str]]) -> Tuple[pd.DataFrame, List[int]]:
    """
    Iterate all patient CSVs, accumulate missingness per group.
    Also compute availability per patient per day for the heatmap.

    Returns:
      - group_summary: DataFrame with columns
          [group_code, group_label, missing_cells, total_cells, missing_pct,
           variables_with_any_missing, variables_total, var_missing_ratio]
      - day_grid_shape: [n_patients, n_days] shape used for availability heatmap construction elsewhere
    """
    files = list_dynamic_csvs(dynamic_dir)
    if not files:
        raise FileNotFoundError(f"No CSV files found in {dynamic_dir}")

    # Prepare accumulators
    group_missing_cells = {g: 0 for g in groups}
    group_total_cells = {g: 0 for g in groups}

    # Track whether each variable (across all patients/days) has any missing values
    var_any_missing = {v: False for cols in groups.values() for v in cols}

    # For availability heatmap, we need the max set of days from the first file
    # We will record per-patient a vector (len=number_of_days_in_first_file),
    # aligning subsequent patients by day index if present; missing days treated as fully missing.
    example_df = pd.read_csv(files[0], header=0, index_col=0)
    # Ensure numeric days, sorted
    example_df.index = pd.to_numeric(example_df.index, errors='coerce')
    example_df = example_df.sort_index()
    day_index = example_df.index.values
    n_days = len(day_index)

    availability_rows = []  # list of np.ndarray (length = n_days)
    patient_ids = []

    # Iterate all patient files
    for fp in files:
        try:
            df = pd.read_csv(fp, header=0, index_col=0)
        except Exception as e:
            print(f"[WARN] Failed to read {fp}: {e}")
            continue

        # Clean / enforce structure
        df.index = pd.to_numeric(df.index, errors='coerce')
        df = df.sort_index()
        # Align to the master day_index; reindex columns to the union needed (groups keys)
        # Keep only columns from the first-file header to ensure consistent variable set
        keep_cols = [v for cols in groups.values() for v in cols]
        df = df.reindex(index=day_index, columns=keep_cols)

        # Availability per day: fraction of non-NA across all variables
        avail_frac = 1.0 - df.isna().mean(axis=1)
        availability_rows.append(avail_frac.values.astype(float))
        patient_ids.append(Path(fp).stem)

        # Group accumulators
        for g, cols in groups.items():
            sub = df[cols]
            miss = sub.isna().sum().sum()
            tot = sub.size
            group_missing_cells[g] += int(miss)
            group_total_cells[g] += int(tot)

        # Track var-level any missing
        var_na = df.isna().any(axis=0)  # per column
        for v, any_na in var_na.items():
            if any_na:
                var_any_missing[v] = True

    # Build summary table
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

    group_summary = pd.DataFrame(rows).sort_values("missing_pct", ascending=False, kind="mergesort").reset_index(drop=True)

    # Availability matrix (patients x days)
    avail_mat = np.vstack(availability_rows) if availability_rows else np.zeros((0, n_days))

    return group_summary, [len(patient_ids), n_days, avail_mat, patient_ids, day_index]


def plot_dynamic_missingness(group_summary: pd.DataFrame):
    """Create a 1x2 figure: (left) bar of missing %, (right) table with exact % and variable-level ratio."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={"width_ratios": [3, 2]})

    # Left: bar chart per group
    x = compute_bar_positions(len(group_summary))
    bars = axes[0].bar(x, group_summary["missing_pct"].values)
    axes[0].set_title("Dynamic Groups: Missing Data (%)")
    axes[0].set_ylabel("Missing (%)")
    axes[0].set_xlabel("Groups")

    axes[0].set_xticks(x)
    xticklabels = [f"{lbl}\n({code})" for lbl, code in zip(group_summary["group_label"], group_summary["group_code"]) ]
    axes[0].set_xticklabels(xticklabels, rotation=0, ha='center')

    # Annotate bars with "% | a/b (vars)"
    labels = [f"{v:.1f}% | {r} vars" for v, r in zip(group_summary["missing_pct"], group_summary["var_missing_ratio"]) ]
    annotate_bars_with_labels(axes[0], bars, labels, pad=2)
    axes[0].grid(axis='y', linestyle='--', alpha=0.4)

    # Right: table
    table_df = group_summary[["group_label", "missing_pct", "var_missing_ratio"]].copy()
    table_df.rename(columns={"group_label": "Group", "missing_pct": "Missing %", "var_missing_ratio": "Vars Missing (any)"}, inplace=True)
    table_df["Missing %"] = table_df["Missing %"].map(lambda x: f"{x:.2f}%")

    axes[1].axis('off')
    axes[1].set_title("Dynamic Groups — Missingness Table")
    tbl = axes[1].table(cellText=table_df.values,
                        colLabels=table_df.columns,
                        loc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.2)

    fig.tight_layout()
    out_path = FIG_DIR / "dynamic_missingness.png"
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f"[Saved] {out_path}")


def plot_availability_heatmap(avail_mat: np.ndarray,
                              patient_ids: List[str],
                              day_index: np.ndarray,
                              y_tick_step: int = 25):
    """
    Plot a patients (rows) x days (cols) heatmap of availability fractions.
    - Values are in [0, 1], representing fraction of non-NA across variables for that day and patient.
    """
    if avail_mat.size == 0:
        print("[WARN] Availability matrix is empty; skipping heatmap.")
        return

    n_patients, n_days = avail_mat.shape
    fig, ax = plt.subplots(1, 1, figsize=(min(16, 8 + n_days * 0.1), min(12, 4 + n_patients * 0.03)))

    im = ax.imshow(avail_mat, aspect='auto', interpolation='nearest', origin='upper', cmap='viridis', vmin=0, vmax=1)
    ax.set_title("Dynamic Data Availability (Patients × Days)")
    ax.set_xlabel("Day")
    ax.set_ylabel("Patient (file ID)")

    # X ticks: show a manageable subset
    # Ensure day_index is sorted; label a few canonical days
    if n_days <= 20:
        ax.set_xticks(np.arange(n_days))
        ax.set_xticklabels([str(int(d)) for d in day_index], rotation=0)
    else:
        # label every ~5th day
        step = max(1, n_days // 10)
        idx = np.arange(0, n_days, step)
        ax.set_xticks(idx)
        ax.set_xticklabels([str(int(day_index[i])) for i in idx], rotation=0)

    # Y ticks: label every y_tick_step-th patient to avoid clutter
    if n_patients <= 40:
        ax.set_yticks(np.arange(n_patients))
        ax.set_yticklabels(patient_ids)
    else:
        idx = np.arange(0, n_patients, y_tick_step)
        ax.set_yticks(idx)
        ax.set_yticklabels([patient_ids[i] for i in idx])

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Availability (fraction non-NA)")

    fig.tight_layout()
    out_path = FIG_DIR / "dynamic_availability_heatmap.png"
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f"[Saved] {out_path}")

# ------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------

def main():
    # 1) Static data
    if not STATIC_PATH.exists():
        print(f"[ERROR] Static file not found: {STATIC_PATH}")
    else:
        static_df = load_static_matrix(STATIC_PATH)
        static_summary = analyze_static_missingness(static_df)
        plot_static_missingness(static_summary)

    # 2) Dynamic data — header from first file defines groups
    if not DYNAMIC_DIR.exists():
        print(f"[ERROR] Dynamic folder not found: {DYNAMIC_DIR}")
        return

    dyn_cols = load_first_dynamic_header(DYNAMIC_DIR)
    groups = build_dynamic_groups(dyn_cols)

    group_summary, avail_pack = analyze_dynamic_missingness(DYNAMIC_DIR, groups)
    plot_dynamic_missingness(group_summary)

    # Availability heatmap
    n_patients, n_days, avail_mat, patient_ids, day_index = avail_pack
    print(f"[Info] Processed {n_patients} patient files; days per file = {n_days}")
    plot_availability_heatmap(avail_mat, patient_ids, day_index)

    # Also export CSV summaries for record/reproducibility
    (FIG_DIR / "tables").mkdir(exist_ok=True)
    # Static
    try:
        static_summary.to_csv(FIG_DIR / "tables" / "static_missingness_summary.csv", index=False)
    except Exception:
        pass
    # Dynamic
    group_summary.to_csv(FIG_DIR / "tables" / "dynamic_missingness_summary.csv", index=False)


if __name__ == "__main__":
    main()
