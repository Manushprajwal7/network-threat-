#!/bin/bash
# Shell runner for E12: Isolation Forest Score Negation & Anomaly Monotonicity Test
set -e
echo "Running E12: Isolation Forest Score Negation & Anomaly Monotonicity Test..."
python ../../experiments/E12_score_sign_test.py
python plot.py
echo "E12_score_sign finished successfully!"
