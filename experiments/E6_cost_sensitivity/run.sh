#!/bin/bash
# Shell runner for E6: Extended False-Blocking Cost Sensitivity Sweep
set -e
echo "Running E6: Extended False-Blocking Cost Sensitivity Sweep..."
python ../../experiments/E6_extended_cost_sensitivity.py
python plot.py
echo "E6_cost_sensitivity finished successfully!"
