import re

def update_assemble():
    path = "paper2/code/assemble_manuscript.py"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # 1. Update Index Terms
    text = text.replace(
        'run_kw_body = p_kw.add_run("Internet of Things, Intrusion Detection Systems, Isolation Forest Contamination, Dynamic Trust Recalibration, Six-Level Security Posture, Cost-Aware Policy Optimization, Monotonic Precision, Multi-Stage Response.")',
        'run_kw_body = p_kw.add_run("Internet of Things, Intrusion Detection Systems, Training Data Purity, Dynamic Trust Recalibration, Six-Level Security Posture, Cost-Aware Policy Optimization, Monotonic Precision, Multi-Stage Response.")'
    )

    # 2. Update Table 1
    text = text.replace(
        'add_table_booktabs(1, "Architectural and quantitative progression comparison between the published baseline [1] and the proposed framework on the CICIoT2023 benchmark.",\n                   "paper2/tables/tab1_paper_comparison.csv",\n                   col_widths=[1.3, 2.5, 2.5, 0.8])',
        'add_table_booktabs(1, "Comparison between published baseline [1] and the proposed framework on the CICIoT2023 benchmark.",\n                   "paper2/tables/tab1_paper_comparison.csv",\n                   col_widths=[1.3, 2.5, 2.5, 0.8])'
    )

    # 3. Update Figure 1
    text = text.replace(
        'add_figure_inline(1, "paper2/figures/fig1_posture_architecture.png",\n                          "Six-level security posture escalation architecture (L0 to L5), illustrating multi-stage evidence synthesis (S = c_topo + c_trust + c_anom + c_conf over sliding windows of W=100 flows), active analytical components, and assigned enforcement tiers from Allow (L0) to Block (L5).")',
        'add_figure_inline(1, "paper2/figures/fig1_posture_architecture.png",\n                          "Multi-stage architecture for security posture escalation (L0–L5) and automated response enforcement over sliding windows (W=100).")'
    )

    # 4. Update Table 2
    text = text.replace(
        'add_table_booktabs(2, "Formal decision-theoretic cost matrix L(a, y) defining unit operational penalties and containment benefits across five response actions in Operational Cost Units (OCU) for benign and attack ground-truth traffic states.",\n                           "paper2/tables/tab2_cost_matrix.csv",\n                           col_widths=[1.0, 1.1, 1.3, 1.2, 2.5])',
        'add_table_booktabs(2, "Decision-theoretic cost matrix L(a, y) defining unit operational penalties and containment benefits across five response actions (OCU).",\n                           "paper2/tables/tab2_cost_matrix.csv",\n                           col_widths=[1.0, 1.1, 1.3, 1.2, 2.5])'
    )

    # 5. Update Table 3
    old_tab3_pat = re.compile(r'add_table_booktabs\(3,\s*\"Controlled quantitative comparison.*?\),\s*col_widths=\[[^\]]+\]\)', re.DOTALL)
    new_tab3 = 'add_table_booktabs(3, "Isolation Forest anomaly detection metrics across model capacities before and after contamination repair (60,000 evaluation flows).",\n                           "paper2/tables/tab3_if_controlled.csv",\n                           col_widths=[1.5, 0.6, 1.2, 0.7, 0.6, 0.8, 0.7, 0.7])'
    text = old_tab3_pat.sub(new_tab3, text)

    # 6. Update Figure 2
    old_fig2_pat = re.compile(r'add_figure_inline\(2,\s*\"paper2/figures/O2_A_if_roc_comparison\.png\",\s*\".*?\"\)', re.DOTALL)
    new_fig2 = 'add_figure_inline(2, "paper2/figures/O2_A_if_roc_comparison.png",\n                          "ROC curves for contaminated and retrained clean Isolation Forest models on the 60,000-flow evaluation stream.")'
    text = old_fig2_pat.sub(new_fig2, text)

    # 7. Update Table 4
    old_tab4_pat = re.compile(r'add_table_booktabs\(4,\s*\"Dynamic trust band distribution.*?\),\s*col_widths=\[[^\]]+\]\)', re.DOTALL)
    new_tab4 = 'add_table_booktabs(4, "Dynamic trust band distribution and discrimination metrics across calibration configurations C0* to C4* under neutral prior T_0 = 100.0.",\n                           "paper2/tables/tab4_trust_neutral.csv",\n                           col_widths=[1.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.7])'
    text = old_tab4_pat.sub(new_tab4, text)

    # 8. Update Figure 3
    old_fig3_pat = re.compile(r'add_figure_inline\(3,\s*\"paper2/figures/O2_B_band_distribution_comparison\.png\",\s*\".*?\"\)', re.DOTALL)
    new_fig3 = 'add_figure_inline(3, "paper2/figures/O2_B_band_distribution_comparison.png",\n                          "Distribution of dynamic trust bands across calibration configurations C0* through C4* under neutral priors (T_0 = 100.0).")'
    text = old_fig3_pat.sub(new_fig3, text)

    # 9. Update Figure 4
    old_fig4_pat = re.compile(r'add_figure_inline\(4,\s*\"paper2/figures/fig10_trust_traces\.png\",\s*\".*?\"\)', re.DOTALL)
    new_fig4 = 'add_figure_inline(4, "paper2/figures/fig10_trust_traces.png",\n                          "Dynamic trust score evolution over consecutive evaluation flows under neutral priors.")'
    text = old_fig4_pat.sub(new_fig4, text)

    # 10. Update Table 5
    old_tab5_pat = re.compile(r'add_table_booktabs\(5,\s*\"Six-level security posture distribution on the sustained volumetric attack-heavy stream.*?\),\s*col_widths=\[[^\]]+\]\)', re.DOTALL)
    new_tab5 = 'add_table_booktabs(5, "Security posture level distribution and attack composition under sustained volumetric attack stream (60,000 flows, W=100).",\n                           "paper2/tables/tab5_posture_attack_heavy.csv",\n                           col_widths=[0.6, 1.3, 0.8, 0.8, 0.9, 0.9, 0.8, 0.9])'
    text = old_tab5_pat.sub(new_tab5, text)

    # 11. Update Table 6
    old_tab6_pat = re.compile(r'add_table_booktabs\(6,\s*\"Six-level security posture distribution on the stratified multi-state benchmark stream.*?\),\s*col_widths=\[[^\]]+\]\)', re.DOTALL)
    new_tab6 = 'add_table_booktabs(6, "Security posture level distribution and attack composition under stratified multi-state benchmark stream (60,000 flows, W=100).",\n                           "paper2/tables/tab6_posture_balanced.csv",\n                           col_widths=[0.6, 1.3, 0.8, 0.8, 0.9, 0.9, 0.8, 0.9])'
    text = old_tab6_pat.sub(new_tab6, text)

    # 12. Update Figure 5
    old_fig5_pat = re.compile(r'add_figure_inline\(5,\s*\"paper2/figures/fig4_two_window_distribution\.png\",\s*\".*?\"\)', re.DOTALL)
    new_fig5 = 'add_figure_inline(5, "paper2/figures/fig4_two_window_distribution.png",\n                          "Posture level distributions under attack-heavy versus stratified multi-state traffic streams (600 batches, W=100).")'
    text = old_fig5_pat.sub(new_fig5, text)

    # 13. Update Table 7
    old_tab7_pat = re.compile(r'add_table_booktabs\(7,\s*\"Comprehensive action-level precision audit.*?\),\s*col_widths=\[[^\]]+\]\)', re.DOTALL)
    new_tab7 = 'add_table_booktabs(7, "Action-level precision and false positive rates under baseline P0, P1, and proposed P2-tier on the multi-state benchmark stream.",\n                           "paper2/tables/tab7_action_precision.csv",\n                           col_widths=[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])'
    text = old_tab7_pat.sub(new_tab7, text)

    # 14. Update Figure 6
    old_fig6_pat = re.compile(r'add_figure_inline\(6,\s*\"paper2/figures/O3_action_precision_bars\.png\",\s*\".*?\"\)', re.DOTALL)
    new_fig6 = 'add_figure_inline(6, "paper2/figures/O3_action_precision_bars.png",\n                          "Action-level precision profiles across enforcement tiers under published baseline P0 and proposed policy P2-tier.")'
    text = old_fig6_pat.sub(new_fig6, text)

    # 15. Update Table 8
    old_tab8_pat = re.compile(r'add_table_booktabs\(8,\s*\"Master policy performance comparison.*?\),\s*col_widths=\[[^\]]+\]\)', re.DOTALL)
    new_tab8 = 'add_table_booktabs(8, "Operational performance comparison across candidate response policies on multi-state and attack-heavy evaluation streams (OCU).",\n                           "paper2/tables/tab8_master_policy.csv",\n                           col_widths=[1.1, 1.8, 0.7, 0.7, 0.7, 0.5, 0.5, 0.5, 0.6])'
    text = old_tab8_pat.sub(new_tab8, text)

    # 16. Update Figure 7
    old_fig7_pat = re.compile(r'add_figure_inline\(7,\s*\"paper2/figures/O3_cost_comparison_bars\.png\",\s*\".*?\"\)', re.DOTALL)
    new_fig7 = 'add_figure_inline(7, "paper2/figures/O3_cost_comparison_bars.png",\n                          "Net operational benefit comparison across candidate policies on multi-state and attack-heavy traffic streams (kOCU).")'
    text = old_fig7_pat.sub(new_fig7, text)

    # 17. Update Figure 8
    old_fig8_pat = re.compile(r'add_figure_inline\(8,\s*\"paper2/figures/O3_L4_escalation_analysis\.png\",\s*\".*?\"\)', re.DOTALL)
    new_fig8 = 'add_figure_inline(8, "paper2/figures/O3_L4_escalation_analysis.png",\n                          "Empirical Pareto frontier of admissible monotonic policies in (Block FPR, Quarantine FPR, Net Benefit) space.")'
    text = old_fig8_pat.sub(new_fig8, text)

    # 18. Update Table 9
    old_tab9_pat = re.compile(r'add_table_booktabs\(9,\s*\"Per-family flow counts.*?\),\s*col_widths=\[[^\]]+\]\)', re.DOTALL)
    new_tab9 = 'add_table_booktabs(9, "Per-family flow counts, enforcement action distributions, and mean dynamic trust scores under policy P2-tier (30,118 attack flows).",\n                           "paper2/tables/tab9_per_family.csv",\n                           col_widths=[1.0, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.8, 0.6, 1.0])'
    text = old_tab9_pat.sub(new_tab9, text)

    # 19. Update Figure 9
    old_fig9_pat = re.compile(r'add_figure_inline\(9,\s*\"paper2/figures/O3_per_family_heatmap\.png\",\s*\".*?\"\)', re.DOTALL)
    new_fig9 = 'add_figure_inline(9, "paper2/figures/O3_per_family_heatmap.png",\n                          "Enforcement action distribution heatmap across eight CICIoT2023 attack families under policy P2-tier.")'
    text = old_fig9_pat.sub(new_fig9, text)

    # 20. Update Table 10
    old_tab10_pat = re.compile(r'add_table_booktabs\(10,\s*\"Cost sensitivity analysis across false-blocking.*?\),\s*col_widths=\[[^\]]+\]\)', re.DOTALL)
    new_tab10 = 'add_table_booktabs(10, "Cost sensitivity analysis across false-blocking scaling factors lambda in [0.2, 5.0] on the multi-state stream.",\n                           "paper2/tables/tab10_cost_sensitivity.csv",\n                           col_widths=[0.7, 1.4, 1.2, 1.3, 1.2, 1.3])'
    text = old_tab10_pat.sub(new_tab10, text)

    # 21. Update Figure 10
    old_fig10_pat = re.compile(r'add_figure_inline\(10,\s*\"paper2/figures/O3_cost_matrix_heatmap\.png\",\s*\".*?\"\)', re.DOTALL)
    new_fig10 = 'add_figure_inline(10, "paper2/figures/O3_cost_matrix_heatmap.png",\n                          "Operational net benefit sensitivity trajectories across false-blocking penalty scaling factors lambda in [0.2, 5.0].")'
    text = old_fig10_pat.sub(new_fig10, text)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated assemble_manuscript.py captions successfully!")

if __name__ == "__main__":
    update_assemble()
