"""
security_level_manager.py — Multi-Signal Evidence Cumulative State Machine (Levels L0–L5)
Implements hierarchical security level assignment based on cumulative evidence
across four orthogonal security signals:
  1. Behavioral Anomaly Accumulation: Isolation Forest anomaly score >= 0.90
  2. Topologically Aware Risk Exposure: Contextual TARP risk >= 0.42
  3. Dynamic Trust Degradation: ADTM Dynamic trust <= 60.0
  4. Classifier Attack Confirmation: XGBoost attack classification with confidence >= 0.95

Formal Cumulative Evidence Formulation:
  S = 1 · I(anom_rate >= 0.28) + 1 · I(TARP >= 0.42) + 1 · I(trust <= 60) + 1 · I(conf_attack_rate >= 0.98)

Level Definitions & Multi-Signal Entry Conditions:
  - L0 (Monitor):   S = 0 (Default operational baseline; zero corroborated threat indicators). Policy: Allow.
  - L1 (Screen):    S = 1 (Single anomaly, topology, or trust signal active). Policy: Alert.
  - L2 (Context):   S = 2 (Two corroborating threat indicators active). Policy: Restrict.
  - L3 (Contain):   S >= 3 (Three or more corroborating threat indicators active). Policy: Quarantine.
  - L4 (Isolate):   S >= 3 AND TARP >= 0.75 AND trust <= 20.0. Policy: Quarantine (Severe). (0% in baseline).
  - L5 (Adaptive):  S >= 3 AND distinct attack families in entity >= 2 AND trust <= 20.0. Policy: Block. (0% in baseline).

Threshold Justifications:
  - TARP >= 0.42:  Inherited from published manuscript Section 3.4 & 5.8 (mean propagated network risk = 0.4200).
  - TARP >= 0.75:  Inherited from Section 3.4 (critical topology hub boundary, exactly 8 critical nodes).
  - Trust <= 60:   Inherited from Table 9 (Moderate-to-Low trust boundary).
  - Trust <= 20:   Inherited from Table 9 (Very Low trust boundary; unreached in baseline reconstruction).
  - Anomaly >= 0.90: Validated on 1,176,851 validation samples (FPR = 6.84% <= 10%, Recall = 85.32% >= 85%).
  - Conf >= 0.95:  Validated on 1,176,851 validation samples (Attack precision = 99.96% >= 90%).
"""

from typing import Dict, List, Optional
import numpy as np


class SecurityLevelManager:
    def __init__(
        self,
        entity_samples: int = 100,
        n_entities: int = 600,
        anom_threshold: float = 0.90,
        conf_threshold: float = 0.95,
        tarp_threshold: float = 0.42,
        trust_threshold: float = 60.0,
        tarp_critical_threshold: float = 0.75,
        trust_critical_threshold: float = 20.0,
        anom_rate_threshold: float = 0.28,
        conf_rate_threshold: float = 0.98,
        enabled_levels: Optional[List[int]] = None,
    ):
        self.entity_samples = entity_samples
        self.n_entities = n_entities
        self.anom_threshold = anom_threshold
        self.conf_threshold = conf_threshold
        self.tarp_threshold = tarp_threshold
        self.trust_threshold = trust_threshold
        self.tarp_critical_threshold = tarp_critical_threshold
        self.trust_critical_threshold = trust_critical_threshold
        self.anom_rate_threshold = anom_rate_threshold
        self.conf_rate_threshold = conf_rate_threshold
        self.enabled_levels = enabled_levels if enabled_levels is not None else [0, 1, 2, 3, 4, 5]

    def evaluate(
        self,
        anomaly_scores: np.ndarray,
        confidences: np.ndarray,
        predicted_labels: np.ndarray,
        trust_scores: np.ndarray,
        tarp_risks: np.ndarray,
        attack_families: Optional[np.ndarray] = None,
        benign_label: int = 1,
    ) -> Dict:
        """
        Evaluates cumulative evidence and assigns security levels per host entity.
        Returns entity and sample level assignments with full signal traces.
        """
        E = self.n_entities
        N = self.entity_samples
        total_eval_samples = E * N

        # Reshape into (E, N) entity matrices
        anom_e = anomaly_scores[:total_eval_samples].reshape(E, N)
        conf_e = confidences[:total_eval_samples].reshape(E, N)
        pred_e = predicted_labels[:total_eval_samples].reshape(E, N)
        trust_e = trust_scores[:total_eval_samples].reshape(E, N)
        tarp_e = tarp_risks[:total_eval_samples].reshape(E, N)[:, 0]  # Static per entity

        is_atk_e = (pred_e != benign_label)

        # ── 1. Evaluate 4 orthogonal evidence signals per entity ─────────────
        # Signal 1: Contextual Topological Threat (TARP >= 0.42)
        c_topo = (tarp_e >= self.tarp_threshold).astype(int)

        # Signal 2: Dynamic Trust Degradation (Trust drops <= 60.0)
        c_trust = (trust_e.min(axis=1) <= self.trust_threshold).astype(int)

        # Signal 3: Behavioral Anomaly Accumulation (Anomaly flows >= 0.90 exceed screening rate)
        anom_frac = (anom_e >= self.anom_threshold).mean(axis=1)
        c_anom = (anom_frac >= self.anom_rate_threshold).astype(int)

        # Signal 4: Confirmed High-Confidence Attack (Attack flows with conf >= 0.95 exceed rate)
        conf_frac = ((conf_e >= self.conf_threshold) & is_atk_e).mean(axis=1)
        c_conf = (conf_frac >= self.conf_rate_threshold).astype(int)

        # ── 2. Compute Cumulative Evidence Score S ───────────────────────────
        S = c_topo + c_trust + c_anom + c_conf

        # ── 3. Assign Hierarchical Security Levels L0–L5 ─────────────────────
        entity_levels = np.zeros(E, dtype=int)

        for e in range(E):
            # Check distinct non-benign attack families within entity window
            distinct_fams = 0
            if attack_families is not None:
                fam_chunk = attack_families[e * N:(e + 1) * N]
                distinct_fams = len(set(f for f in fam_chunk if f != "Benign"))

            # L5: Adaptive Block (S >= 3 AND multi-vector confirmation AND severe trust degradation <= 20)
            if (
                5 in self.enabled_levels
                and S[e] >= 3
                and distinct_fams >= 2
                and trust_e[e].min() <= self.trust_critical_threshold
            ):
                entity_levels[e] = 5
            # L4: Critical Topology Isolation (S >= 3 AND TARP >= 0.75 AND trust <= 20)
            elif (
                4 in self.enabled_levels
                and S[e] >= 3
                and tarp_e[e] >= self.tarp_critical_threshold
                and trust_e[e].min() <= self.trust_critical_threshold
            ):
                entity_levels[e] = 4
            # L3: Containment (Cumulative evidence score S >= 3)
            elif 3 in self.enabled_levels and S[e] >= 3:
                entity_levels[e] = 3
            # L2: Contextual Restriction (Cumulative evidence score S == 2)
            elif 2 in self.enabled_levels and S[e] == 2:
                entity_levels[e] = 2
            # L1: Screening / Alert (Cumulative evidence score S == 1)
            elif 1 in self.enabled_levels and S[e] == 1:
                entity_levels[e] = 1
            # L0: Default Monitor (S == 0)
            else:
                entity_levels[e] = 0

        # Expand entity level to individual samples
        sample_levels = np.repeat(entity_levels, N)

        return {
            "entity_levels": entity_levels,
            "sample_levels": sample_levels,
            "entity_scores": S,
            "signals": {
                "c_topo": c_topo,
                "c_trust": c_trust,
                "c_anom": c_anom,
                "c_conf": c_conf,
            },
            "metrics": {
                "e_tarp": tarp_e,
                "e_trust_mean": trust_e.mean(axis=1),
                "e_trust_min": trust_e.min(axis=1),
                "e_anom_mean": anom_e.mean(axis=1),
                "anom_frac": anom_frac,
                "conf_frac": conf_frac,
            },
        }
