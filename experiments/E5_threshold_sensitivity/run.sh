#!/bin/bash
# Shell runner for E5: Security Posture Escalation Threshold Sensitivity Sweep
set -e
echo "Running E5: Security Posture Escalation Threshold Sensitivity Sweep..."
python ../../experiments/E5_threshold_sensitivity.py
python plot.py
echo "E5_threshold_sensitivity finished successfully!"
