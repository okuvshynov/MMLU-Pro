#!/usr/bin/env python3
"""
Analyze correctness patterns between different models.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any


def load_combined_dataset(filepath: Path) -> List[Dict[str, Any]]:
    """Load combined dataset."""
    with open(filepath, 'r') as f:
        return json.load(f)


def analyze_correctness_patterns(data: List[Dict[str, Any]]):
    """Analyze correctness patterns between different models."""
    
    # Count different patterns
    patterns = {
        'both_correct': 0,
        'both_wrong': 0,
        'nothink_only': 0,  # nothink correct, think wrong
        'think_only': 0,    # think correct, nothink wrong
    }
    
    # Lists to store question_ids for each pattern
    pattern_questions = {
        'both_correct': [],
        'both_wrong': [],
        'nothink_only': [],
        'think_only': [],
    }
    
    # Analyze bias patterns if available
    bias_patterns = {}
    bias_columns = []
    
    # Detect all bias columns dynamically
    if data:
        all_columns = list(data[0].keys())
        for col in all_columns:
            if col.startswith('cs_think_bias_') and col.endswith('_correct'):
                bias_name = col.replace('_correct', '')
                bias_columns.append(bias_name)
                # Initialize patterns for this bias model
                bias_patterns[f'{bias_name}_unique'] = 0  # correct when both nothink and think are wrong
                bias_patterns[f'{bias_name}_only_vs_think'] = 0  # correct, think wrong
    
    for row in data:
        question_id = row['question_id']
        nothink_correct = row.get('cs_nothink_correct', 0)
        think_correct = row.get('cs_think_correct', 0)
        
        # Classify pattern
        if nothink_correct and think_correct:
            patterns['both_correct'] += 1
            pattern_questions['both_correct'].append(question_id)
        elif not nothink_correct and not think_correct:
            patterns['both_wrong'] += 1
            pattern_questions['both_wrong'].append(question_id)
            
            # Check if bias versions got it right
            for bias_name in bias_columns:
                if row.get(f'{bias_name}_correct', 0):
                    bias_patterns[f'{bias_name}_unique'] += 1
                
        elif nothink_correct and not think_correct:
            patterns['nothink_only'] += 1
            pattern_questions['nothink_only'].append(question_id)
        else:  # think correct, nothink wrong
            patterns['think_only'] += 1
            pattern_questions['think_only'].append(question_id)
        
        # Check bias vs think patterns
        for bias_name in bias_columns:
            bias_correct = row.get(f'{bias_name}_correct', 0)
            if bias_correct and not think_correct:
                bias_patterns[f'{bias_name}_only_vs_think'] += 1
    
    # Calculate totals
    total = len(data)
    
    # Print results
    print("=" * 60)
    print("CORRECTNESS PATTERN ANALYSIS")
    print("=" * 60)
    print(f"Total questions analyzed: {total}")
    print()
    
    print("Main Patterns:")
    print(f"  Both correct:        {patterns['both_correct']:4d} ({patterns['both_correct']/total*100:5.1f}%)")
    print(f"  Both wrong:          {patterns['both_wrong']:4d} ({patterns['both_wrong']/total*100:5.1f}%)")
    print(f"  NoThink only:        {patterns['nothink_only']:4d} ({patterns['nothink_only']/total*100:5.1f}%) <- NoThink correct, Think wrong")
    print(f"  Think only:          {patterns['think_only']:4d} ({patterns['think_only']/total*100:5.1f}%) <- Think correct, NoThink wrong")
    
    # Calculate accuracy comparison
    nothink_total = sum(row.get('cs_nothink_correct', 0) for row in data)
    think_total = sum(row.get('cs_think_correct', 0) for row in data)
    
    print()
    print("Overall Accuracy:")
    print(f"  NoThink:             {nothink_total:4d} ({nothink_total/total*100:5.1f}%)")
    print(f"  Think:               {think_total:4d} ({think_total/total*100:5.1f}%)")
    print(f"  Accuracy difference: {(think_total - nothink_total)/total*100:+5.1f}% (Think vs NoThink)")
    
    if bias_columns:
        print()
        print("Bias Model Analysis:")
        for bias_name in sorted(bias_columns):
            bias_total = sum(row.get(f'{bias_name}_correct', 0) for row in data)
            # Extract the bias value from the name (e.g., "cs_think_bias_19" -> "19")
            bias_value = bias_name.split('_')[-1]
            print(f"  Bias{bias_value} total correct: {bias_total:4d} ({bias_total/total*100:5.1f}%)")
            print(f"    Unique wins (when both fail): {bias_patterns[f'{bias_name}_unique']:4d}")
            print(f"    Better than Think:            {bias_patterns[f'{bias_name}_only_vs_think']:4d}")
    
    # Save detailed results
    output_file = 'correctness_patterns.json'
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_questions': total,
                'patterns': patterns,
                'accuracies': {
                    'nothink': nothink_total / total if total > 0 else 0,
                    'think': think_total / total if total > 0 else 0,
                },
                'bias_patterns': bias_patterns if bias_columns else {}
            },
            'question_ids': {
                'nothink_only_correct': pattern_questions['nothink_only'][:10],  # First 10 examples
                'think_only_correct': pattern_questions['think_only'][:10],
                'both_wrong': pattern_questions['both_wrong'][:10],
            }
        }, f, indent=2)
    
    print(f"\nDetailed results saved to {output_file}")
    print("\nFirst 5 questions where NoThink is correct but Think is wrong:")
    for i, qid in enumerate(pattern_questions['nothink_only'][:5]):
        print(f"  {i+1}. Question ID: {qid}")


def main():
    parser = argparse.ArgumentParser(description='Analyze correctness patterns')
    parser.add_argument('--input', '-i', default='combined_dataset.json',
                        help='Path to combined dataset (default: combined_dataset.json)')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found")
        print("Please run combine_datasets.py first to create the combined dataset")
        return
    
    # Load and analyze
    data = load_combined_dataset(Path(args.input))
    analyze_correctness_patterns(data)


if __name__ == "__main__":
    main()