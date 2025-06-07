# MMLU-Pro Think Data Analysis

This directory contains scripts for analyzing and visualizing MMLU-Pro dataset results comparing "think" and "no-think" model outputs.

## Prerequisites

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure you have a tokenization service running at `http://localhost:8080/tokenize` (or specify a different URL)

## Scripts

### 1. combine_datasets.py
Combines multiple JSON files into a single dataset with correctness and token count columns.

**Usage:**
```bash
python combine_datasets.py [--tokenize-url URL] [--output FILE]
```

**Output columns:**
- `question_id`: Question identifier
- `<filename>_correct`: 1 if answer equals prediction, 0 otherwise
- `<filename>_n_tokens`: Token count from tokenization service

### 2. summarize.py
Summarizes the combined dataset by calculating totals and averages.

**Usage:**
```bash
python summarize.py [input_file] [--output FILE]
```

### 3. simulate_selection.py
Simulates random selection between cs_think and cs_nothink datasets with configurable probability.

**Usage:**
```bash
python simulate_selection.py [-p PROBABILITY] [-n REPEATS] [--seed SEED]
```

**Parameters:**
- `-p`: Probability of selecting cs_think (default: 0.5)
- `-n`: Number of simulation runs (default: 1000)
- `--seed`: Random seed for reproducibility

### 4. visualize_accuracy_tokens.py
Creates a scatter plot showing accuracy vs token usage for real and simulated data.

**Usage:**
```bash
python visualize_accuracy_tokens.py [--input FILE] [--simulations PATTERN]
```

**Output:**
- `accuracy_vs_tokens_scatter.png`: Scatter plot image
- `accuracy_vs_tokens_scatter.pdf`: High-quality PDF version

### 5. run_analysis.py
Runs the complete analysis pipeline automatically.

**Usage:**
```bash
python run_analysis.py [tokenize_url]
```

## Data Files

- `cs_nothink.json`: Results without chain-of-thought
- `cs_think.json`: Results with chain-of-thought
- `cs_think_bias_19.json`: Results with bias setting 19
- `cs_think_bias_20.json`: Results with bias setting 20

## Visualization Details

The scatter plot shows:
- **Red circles**: cs_nothink results
- **Teal squares**: cs_think results
- **Teal triangles**: cs_think_bias results (up=19, down=20)
- **Light teal dots**: Simulation results
- **Dashed line**: Theoretical mixing line between think and nothink

## Example Workflow

```bash
# Run complete analysis
python run_analysis.py

# Or run steps individually:
python combine_datasets.py
python summarize.py --output summary.json
python simulate_selection.py -p 0.7 -n 5000
python visualize_accuracy_tokens.py
```