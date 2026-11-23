#!/bin/bash
# Shell runner for E4: ADTM Component Weight Sensitivity Analysis
set -e
echo "Running E4: ADTM Component Weight Sensitivity Analysis..."
python ../../experiments/E4_adtm_weight_sensitivity.py
python plot.py
echo "E4_adtm_weight finished successfully!"
