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
    bias_patterns = {
        'bias19_unique': 0,  # bias19 correct when both nothink and think are wrong
        'bias20_unique': 0,  # bias20 correct when both nothink and think are wrong
        'bias19_only_vs_think': 0,  # bias19 correct, think wrong
        'bias20_only_vs_think': 0,  # bias20 correct, think wrong
    }
    
    # Check if bias columns exist
    has_bias19 = 'cs_think_bias_19_correct' in data[0] if data else False
    has_bias20 = 'cs_think_bias_20_correct' in data[0] if data else False
    
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
            if has_bias19 and row.get('cs_think_bias_19_correct', 0):
                bias_patterns['bias19_unique'] += 1
            if has_bias20 and row.get('cs_think_bias_20_correct', 0):
                bias_patterns['bias20_unique'] += 1
                
        elif nothink_correct and not think_correct:
            patterns['nothink_only'] += 1
            pattern_questions['nothink_only'].append(question_id)
        else:  # think correct, nothink wrong
            patterns['think_only'] += 1
            pattern_questions['think_only'].append(question_id)
        
        # Check bias vs think patterns
        if has_bias19:
            bias19_correct = row.get('cs_think_bias_19_correct', 0)
            if bias19_correct and not think_correct:
                bias_patterns['bias19_only_vs_think'] += 1
                
        if has_bias20:
            bias20_correct = row.get('cs_think_bias_20_correct', 0)
            if bias20_correct and not think_correct:
                bias_patterns['bias20_only_vs_think'] += 1
    
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
    
    if has_bias19 or has_bias20:
        print()
        print("Bias Model Analysis:")
        if has_bias19:
            bias19_total = sum(row.get('cs_think_bias_19_correct', 0) for row in data)
            print(f"  Bias19 total correct: {bias19_total:4d} ({bias19_total/total*100:5.1f}%)")
            print(f"    Unique wins (when both fail): {bias_patterns['bias19_unique']:4d}")
            print(f"    Better than Think:            {bias_patterns['bias19_only_vs_think']:4d}")
            
        if has_bias20:
            bias20_total = sum(row.get('cs_think_bias_20_correct', 0) for row in data)
            print(f"  Bias20 total correct: {bias20_total:4d} ({bias20_total/total*100:5.1f}%)")
            print(f"    Unique wins (when both fail): {bias_patterns['bias20_unique']:4d}")
            print(f"    Better than Think:            {bias_patterns['bias20_only_vs_think']:4d}")
    
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
                'bias_patterns': bias_patterns if (has_bias19 or has_bias20) else {}
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