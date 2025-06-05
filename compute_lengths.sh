bias=$1

jq 'map(.model_outputs |= length | del(.options, .question))' eval_results/Qwen3-30B-A3B-UD-Q6_K_XL_think_bias_$bias/psychology_result.json > eval_results/Qwen3-30B-A3B-UD-Q6_K_XL_think_bias_$bias/psychology_result_lengths.json

