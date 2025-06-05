#!/bin/bash

# qwen3-specific </think> token id == 151668

bias=$1

python evaluate_from_api.py         \
     --model_name local_llamacpp    \
     --output_dir eval_results/Qwen3-30B-A3B-UD-Q6_K_XL_think_bias_$bias \
     --assigned_subjects all \
     --logit_bias_token 151668      \
     --logit_bias $bias             
