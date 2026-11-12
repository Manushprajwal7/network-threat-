#!/bin/bash
# Shell runner for E8: Posture Level L5 Theoretical & Empirical Population Proof
set -e
echo "Running E8: Posture Level L5 Theoretical & Empirical Population Proof..."
python ../../experiments/E8_l5_population_test.py
python plot.py
echo "E8_l5_population finished successfully!"
