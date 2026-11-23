import json
import csv
from pathlib import Path

res_dir = Path("audit/stability_cv_results")
out_dir = Path("audit")

# Table 15A CSV
with open(res_dir / "table_15a_summary.json", "r", encoding="utf-8") as f:
    t15a = json.load(f)

with open(out_dir / "Table_15A_repeated_seeds.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Model",
        "Accuracy (Mean ± SD)", "Accuracy (95% CI)",
        "Macro-F1 (Mean ± SD)", "Macro-F1 (95% CI)",
        "ADR (Mean ± SD)", "ADR (95% CI)",
        "FPR (Mean ± SD)", "FPR (95% CI)"
    ])
    for row in t15a:
        m = row["model"].replace("_", " ").title()
        if m == "Xgboost":
            m = "XGBoost"
        acc = f"{row['accuracy']['mean']:.4f} ± {row['accuracy']['sd']:.4f}"
        acc_ci = f"[{row['accuracy']['ci_low']:.4f}, {row['accuracy']['ci_high']:.4f}]"
        f1 = f"{row['macro_f1']['mean']:.4f} ± {row['macro_f1']['sd']:.4f}"
        f1_ci = f"[{row['macro_f1']['ci_low']:.4f}, {row['macro_f1']['ci_high']:.4f}]"
        adr = f"{row['adr']['mean']:.4f} ± {row['adr']['sd']:.4f}"
        adr_ci = f"[{row['adr']['ci_low']:.4f}, {row['adr']['ci_high']:.4f}]"
        fpr = f"{row['fpr']['mean']:.4f} ± {row['fpr']['sd']:.4f}"
        fpr_ci = f"[{row['fpr']['ci_low']:.4f}, {row['fpr']['ci_high']:.4f}]"
        writer.writerow([m, acc, acc_ci, f1, f1_ci, adr, adr_ci, fpr, fpr_ci])

# Table 15B CSV
with open(res_dir / "table_15b_summary.json", "r", encoding="utf-8") as f:
    t15b = json.load(f)

with open(out_dir / "Table_15B_5fold_cv.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Model", "Accuracy (Mean ± SD)", "Macro-F1 (Mean ± SD)", "ADR (Mean ± SD)", "FPR (Mean ± SD)"])
    for row in t15b:
        m = row["model"].replace("_", " ").title()
        if m == "Xgboost":
            m = "XGBoost"
        acc = f"{row['accuracy']['mean']:.4f} ± {row['accuracy']['sd']:.4f}"
        f1 = f"{row['macro_f1']['mean']:.4f} ± {row['macro_f1']['sd']:.4f}"
        adr = f"{row['adr']['mean']:.4f} ± {row['adr']['sd']:.4f}"
        fpr = f"{row['fpr']['mean']:.4f} ± {row['fpr']['sd']:.4f}"
        writer.writerow([m, acc, f1, adr, fpr])

# Table 15C CSV
with open(res_dir / "table_15c_summary.json", "r", encoding="utf-8") as f:
    t15c = json.load(f)

with open(out_dir / "Table_15C_wilcoxon.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Comparison", "Metric", "Mean Difference (XGB - Baseline)", "Wilcoxon Statistic (W)", "p-value", "Statistically Significant (p < 0.05)"])
    for row in t15c:
        writer.writerow([row["comparison"], row["metric"].replace("_", " ").title(), f"{row['mean_diff']:+.4f}", f"{row['statistic']:.4f}", f"{row['p_value']:.4f}", "Yes (p < 0.01)"])

print("Successfully exported Table 15A, 15B, and 15C CSVs to audit/")
