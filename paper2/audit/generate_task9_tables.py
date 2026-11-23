import os
import shutil
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES_DIR = ROOT / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

def generate_task9_tables():
    print("=== GENERATING TASK 9 TABLES AND CSV ARTIFACTS ===")
    
    # 1. Level Assignment Table
    level_rows = [
        {
            "Level": "L0",
            "Name": "Nominal Surveillance",
            "Evidence Score S": "S = 0",
            "Trust Condition": "T_mean >= 60.0",
            "Centrality R": "Any R",
            "Operational Meaning": "Zero threat evidence; healthy behavioral trust; normal flow routing",
            "Default Action (P1 / P2-tier)": "Allow"
        },
        {
            "Level": "L1",
            "Name": "Heightened Surveillance",
            "Evidence Score S": "S = 1 (or S = 0)",
            "Trust Condition": "T_mean < 60.0 (if S = 0)",
            "Centrality R": "Any R",
            "Operational Meaning": "Single isolated signal (often c_topo) or mild trust decay; enhanced logging",
            "Default Action (P1 / P2-tier)": "Alert"
        },
        {
            "Level": "L2",
            "Name": "Elevated Monitoring",
            "Evidence Score S": "S = 2",
            "Trust Condition": "Any T",
            "Centrality R": "Any R",
            "Operational Meaning": "Two concurrent signals (e.g. anomaly + trust decay); rate limiting / deep inspection",
            "Default Action (P1 / P2-tier)": "Restrict"
        },
        {
            "Level": "L3",
            "Name": "Active Containment",
            "Evidence Score S": "S >= 3",
            "Trust Condition": "T_mean > 20.0",
            "Centrality R": "Any R",
            "Operational Meaning": "Three or more concurrent signals with moderate trust remaining; isolated sandboxing",
            "Default Action (P1 / P2-tier)": "Quarantine"
        },
        {
            "Level": "L4",
            "Name": "Severe Edge Containment",
            "Evidence Score S": "S >= 3",
            "Trust Condition": "T_mean <= 20.0",
            "Centrality R": "R_mean < 0.75",
            "Operational Meaning": "Acute threat saturation with depleted trust on peripheral edge gateways; port isolation",
            "Default Action (P1 / P2-tier)": "Block (P2-tier) / Quar (P1)"
        },
        {
            "Level": "L5",
            "Name": "Critical Backbone Hub Quarantine",
            "Evidence Score S": "S >= 3",
            "Trust Condition": "T_mean <= 20.0",
            "Centrality R": "R_mean >= 0.75",
            "Operational Meaning": "Acute threat saturation on high-centrality core SDN transit hubs; immediate BGP/flow shutdown",
            "Default Action (P1 / P2-tier)": "Block"
        }
    ]
    df_lvl = pd.DataFrame(level_rows)
    df_lvl.to_csv(TABLES_DIR / "tab_level_assignment.csv", index=False)
    print("Saved tab_level_assignment.csv")
    
    # 2. Evaluation Regimes Definition Table
    regime_rows = [
        {
            "Regime Identifier": "Balanced Multi-State",
            "Total Flows": "60,000",
            "Batches (W=100)": "600",
            "Attack Base Rate": "50.20%",
            "Batch Composition Structure": "180 pure benign, 240 mixed (binomial p=0.50), 180 pure attack batches",
            "Operational Purpose": "Evaluates graduated posture escalation and precision monotonicity across threat phases"
        },
        {
            "Regime Identifier": "Attack-Heavy Surge",
            "Total Flows": "60,000",
            "Batches (W=100)": "600",
            "Attack Base Rate": "97.60%",
            "Batch Composition Structure": "Contiguous test slice matching empirical high-rate volumetric DDoS/Mirai floods",
            "Operational Purpose": "Evaluates high-volume threat containment benefit and measures collateral benign blocking"
        },
        {
            "Regime Identifier": "Multi-State Phase Transition",
            "Total Flows": "60,000",
            "Batches (W=100)": "600",
            "Attack Base Rate": "50.20%",
            "Batch Composition Structure": "Sequential phase transitions (Nominal -> Probe -> Lateral -> Flood -> Recovery)",
            "Operational Purpose": "Validates hysteresis latching and cooldown de-escalation over continuous time"
        },
        {
            "Regime Identifier": "Unstratified Shuffled",
            "Total Flows": "60,000",
            "Batches (W=100)": "600",
            "Attack Base Rate": "50.20%",
            "Batch Composition Structure": "60k flows randomly interleaved without batch purity stratification",
            "Operational Purpose": "Assesses sensitivity to batch structuring and measures worst-case unstratified disruption"
        },
        {
            "Regime Identifier": "Pure Volumetric Flood",
            "Total Flows": "60,000",
            "Batches (W=100)": "600",
            "Attack Base Rate": "100.00%",
            "Batch Composition Structure": "60,000 consecutive attack flows across DDoS, DoS, and Mirai attack families",
            "Operational Purpose": "Measures maximum threat containment reward under total malicious link saturation"
        }
    ]
    df_reg = pd.DataFrame(regime_rows)
    df_reg.to_csv(TABLES_DIR / "tab_regimes_definition.csv", index=False)
    print("Saved tab_regimes_definition.csv")
    
    # 3. Topology Seed & Confound Table
    shutil.copy(ROOT / "audit" / "outputs" / "task2_topology_confound_summary.csv", TABLES_DIR / "tab_topology_confound_summary.csv")
    print("Copied tab_topology_confound_summary.csv")
    
    # 4. Full 70-Policy Table
    shutil.copy(ROOT / "clean_experiments_isolated" / "tables" / "tab5_policy_sweep_all70.csv", TABLES_DIR / "tab_full_70_policies.csv")
    print("Copied tab_full_70_policies.csv")

if __name__ == "__main__":
    generate_task9_tables()
