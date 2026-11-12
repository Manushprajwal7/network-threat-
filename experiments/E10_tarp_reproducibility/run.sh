#!/bin/bash
# Shell runner for E10: TARP Graph Topology & PageRank Distribution Reproducibility
set -e
echo "Running E10: TARP Graph Topology & PageRank Distribution Reproducibility..."
python ../../experiments/E10_tarp_reproducibility.py
python plot.py
echo "E10_tarp_reproducibility finished successfully!"
