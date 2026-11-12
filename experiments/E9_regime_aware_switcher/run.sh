#!/bin/bash
# Shell runner for E9: Minimal Online Regime-Aware Dynamic Policy Switcher
set -e
echo "Running E9: Minimal Online Regime-Aware Dynamic Policy Switcher..."
python ../../experiments/E9_regime_aware_switcher.py
python plot.py
echo "E9_regime_aware_switcher finished successfully!"
