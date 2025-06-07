#!/usr/bin/env python3
"""
Summarize combined dataset by summing all values by key (except question_id).
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any


def summarize_dataset(input_file: str, output_file: str = None):
    """Load combined dataset and create summary statistics."""
    # Load the combined dataset
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    if not data:
        print("Error: Dataset is empty")
        return
    
    # Initialize summary dictionary
    summary = {}
    
    # Get all keys from the first item (except question_id)
    keys_to_sum = [k for k in data[0].keys() if k != 'question_id']
    
    # Initialize sums
    for key in keys_to_sum:
        summary[key] = 0
    
    # Sum all values
    for row in data:
        for key in keys_to_sum:
            if key in row:
                summary[key] += row[key]
    
    # Add metadata
    summary['total_questions'] = len(data)
    
    # Calculate averages for correctness columns
    averages = {}
    for key in keys_to_sum:
        if key.endswith('_correct'):
            avg_key = key.replace('_correct', '_accuracy')
            averages[avg_key] = summary[key] / len(data) if len(data) > 0 else 0
    
    # Combine summary and averages
    final_summary = {**summary, **averages}
    
    # Print summary
    print("\nDataset Summary:")
    print(f"Total questions: {summary['total_questions']}")
    print("\nSums by column:")
    for key in sorted(keys_to_sum):
        print(f"  {key}: {summary[key]}")
    
    if averages:
        print("\nAccuracy metrics:")
        for key in sorted(averages.keys()):
            print(f"  {key}: {averages[key]:.4f} ({averages[key]*100:.2f}%)")
    
    # Save to file if output path provided
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(final_summary, f, indent=2)
        print(f"\nSummary saved to {output_file}")
    
    return final_summary


def main():
    parser = argparse.ArgumentParser(description='Summarize combined dataset')
    parser.add_argument('input', nargs='?', default='combined_dataset.json',
                        help='Input file path (default: combined_dataset.json)')
    parser.add_argument('--output', '-o', 
                        help='Output file path (optional, will print to console if not specified)')
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found")
        return
    
    summarize_dataset(args.input, args.output)


if __name__ == "__main__":
    main()