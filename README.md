## This is a fork! Check original MMLU repo

## Experiment setup

This is an experimental fork to understand the inference-time tradeoff between thinking time and quality for LLM models with thinking like Qwen3.

Intuition: rather than disabling thinking with ```/nothink``` or somehow tuning model, we can artifially adjust the logit value for ```</think>```.
This way, we'll nidge model to stop 'thinking' and produce the final, user-visible output, without hardcoding the limit/budget and allow to think when it's really worth it.

Tweaking the value of this bias, we can achieve different tradeoffs between thinking time and quality.

Setup for current run:
* Use MMLU-Pro benchmark. As of Jun 6, only psychology section is complete (https://github.com/TIGER-AI-Lab/MMLU-Pro)
* Use llama.cpp server for inference. It is easy to provide bias for a token. (https://github.com/ggml-org/llama.cpp/tree/master/tools/server)
* Use Qwen3-30B_A3B model, Unsloth's Q6 quant (https://huggingface.co/unsloth/Qwen3-30B-A3B-GGUF)
* Running on Apple M2 Ultra
* Start with bias = 0, and extreme value of bias = 20 to confirm it works. Do a more thorough parameter search at the area where we observe thinking time changes
* Use temp = 0

Limitations:
* Haven't run with '/nothink' yet to compare.
* Only one section completed, it takes a while, CS will be next to run;
* Bias is static. There's no dynamic schedule for bias adjustment;
* Bias is applied for every token, even after one </think> was already inserted;
* The dataset/benchmark/model combination is not particularly sensitive to the thinking amount, 


## Results


## Instructions to reproduce/notes

1. Get and build llama.cpp server https://github.com/ggml-org/llama.cpp/tree/master/tools/server
2. Get the model https://huggingface.co/unsloth/Qwen3-30B-A3B-GGUF
3. Start the server:
4. Start the MMLU script.
5. Once done, we can process the data - it uses same llama server to tokenize <think></think> content



qwen 3 </think> token:
```
(base) studio ~ % curl http://127.0.0.1:8080/tokenize -H "Content-Type: application/json" -d '{"content": "</think>"}'
{"tokens":[151668]}%
(base) studio ~ % curl http://127.0.0.1:8080/detokenize -H "Content-Type: application/json" -d '{"tokens": [151668]}'
{"content":"</think>"}%
```

