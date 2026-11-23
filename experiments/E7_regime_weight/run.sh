#!/bin/bash
# Shell runner for E7: Evaluation Stream Mixture Weight Sensitivity
set -e
echo "Running E7: Evaluation Stream Mixture Weight Sensitivity..."
python ../../experiments/E7_regime_weight_sensitivity.py
python plot.py
echo "E7_regime_weight finished successfully!"
