#!/bin/bash

model=$1
n_repeats=${2:-1}

cd ../../

for run in $(seq 1 $n_repeats); do
    echo "Running evaluation $run of $n_repeats..."
    python evaluate_local_api.py                 \
         --model_name "$model"                   \
         --output_dir "eval_results/$model/$run"
done
