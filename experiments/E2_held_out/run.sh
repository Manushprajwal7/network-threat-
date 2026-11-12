#!/bin/bash
# Shell runner for E2: Held-Out Balanced Test Partition Evaluation
set -e
echo "Running E2: Held-Out Balanced Test Partition Evaluation..."
python ../../experiments/E2_held_out_balanced.py
python plot.py
echo "E2_held_out finished successfully!"
