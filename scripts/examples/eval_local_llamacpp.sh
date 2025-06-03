#!/bin/bash

cd ../../

python evaluate_from_api.py \
     --model_name local_llamacpp \
     --output_dir eval_results/Qwen3-30B-A3B-UD-Q6_K_XL \
     --assigned_subjects all
