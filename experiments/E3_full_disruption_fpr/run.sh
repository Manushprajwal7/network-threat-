#!/bin/bash
# Shell runner for E3: Full Disruptive False Positive Rate Audit Across 70 Policies
set -e
echo "Running E3: Full Disruptive False Positive Rate Audit Across 70 Policies..."
python ../../experiments/E3_full_disruption_fpr.py
python plot.py
echo "E3_full_disruption_fpr finished successfully!"
