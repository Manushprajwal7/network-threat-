#!/bin/bash
# Shell runner for E11: Exact Closed-Form Wilson Score 95% Confidence Intervals
set -e
echo "Running E11: Exact Closed-Form Wilson Score 95% Confidence Intervals..."
python ../../experiments/E11_wilson_ci.py
python plot.py
echo "E11_wilson_ci finished successfully!"
