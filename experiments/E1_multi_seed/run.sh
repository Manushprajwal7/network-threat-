#!/bin/bash
# Shell runner for E1: Multi-Seed Stability Suite across 5 Random Seeds
set -e
echo "Running E1: Multi-Seed Stability Suite across 5 Random Seeds..."
python ../../experiments/E1_multiseed_stability.py
python plot.py
echo "E1_multi_seed finished successfully!"
