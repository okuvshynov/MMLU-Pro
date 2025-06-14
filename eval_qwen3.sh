#!/bin/bash

# qwen3-specific </think> token id == 151668

bias=$1

python evaluate_from_api.py         \
     --model_name local_llamacpp    \
     --output_dir eval_results/Qwen3-30B-A3B-4bit-DWQ-053125_$bias \
     --assigned_subjects "computer science" \
     --logit_bias_token 151668      \
     --logit_bias $bias             
