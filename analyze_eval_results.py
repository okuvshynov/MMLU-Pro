#!/usr/bin/env python3
import json
import re
from pathlib import Path
from statistics import mean

def analyze_eval_results():
    """Analyze eval_results JSON files and extract requested metrics."""
    eval_results_dir = Path("/Users/oleksandr/projects/MMLU-Pro/eval_results")
    
    # Find all directories matching pattern *_bias_NUMBER
    results = []
    
    for dir_path in eval_results_dir.glob("*_bias_*"):
        if not dir_path.is_dir():
            continue
            
        # Extract bias number from directory name
        bias_match = re.search(r'_bias_(\d+(?:\.\d+)?)$', dir_path.name)
        if not bias_match:
            continue
        bias_number = float(bias_match.group(1))
        
        # Find all *_result.json files in this directory
        for json_file in dir_path.glob("*_result.json"):
            # Extract category from filename
            category_match = re.match(r'(.+)_result\.json$', json_file.name)
            if not category_match:
                continue
            category = category_match.group(1)
            
            # Read and analyze JSON file
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Count matches where answer == pred
                match_count = 0
                model_output_lengths = []
                
                for item in data:
                    if item.get('answer') == item.get('pred'):
                        match_count += 1
                    
                    # Get model_outputs length (note: field is 'model_outputs' not 'model_output')
                    model_outputs = item.get('model_outputs', '')
                    if model_outputs:
                        model_output_lengths.append(len(model_outputs))
                
                # Calculate average model_output length
                avg_length = mean(model_output_lengths) if model_output_lengths else 0
                
                results.append({
                    'end_think_bias': bias_number,
                    'category': category,
                    'correct': match_count,
                    'total': len(data),
                    'pass_rate': match_count / len(data) if len(data) > 0 else 0,
                    'avg_output_len': avg_length
                })
                
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
    
    # Print header
    print("end_think_bias, category, correct, total, pass_rate, avg_output_len")
   
    # Print results
    for result in results:
        print(f"{result['end_think_bias']}, {result['category']}, {result['correct']}, {result['total']}, {result['pass_rate']:.4f}, {result['avg_output_len']:.2f}")

if __name__ == "__main__":
    analyze_eval_results()
