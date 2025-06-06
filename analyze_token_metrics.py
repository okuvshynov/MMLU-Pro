#!/usr/bin/env python3
"""
Analyze token metrics for a single MMLU-Pro evaluation result file.
"""

import argparse
import json
import re
import csv
import requests
from typing import Dict, List, Optional
from pathlib import Path


def extract_think_content(text: str) -> Optional[str]:
    """Extract content between <think>...</think> tags."""
    match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
    return match.group(1) if match else None


def tokenize_text(text: str, tokenize_url: str) -> List[int]:
    """Send text to tokenization service and return token list."""
    try:
        response = requests.post(tokenize_url, json={'content': text})
        response.raise_for_status()
        return response.json()['tokens']
    except Exception as e:
        print(f"Error tokenizing text: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Analyze token metrics for MMLU-Pro result file')
    parser.add_argument('file', help='Path to result JSON file')
    parser.add_argument('--tokenize-url', default='http://localhost:8080/tokenize',
                        help='URL for tokenization service (default: http://localhost:8080/tokenize)')
    parser.add_argument('--output', help='Output CSV filename (default: <input>_metrics.csv)')
    
    args = parser.parse_args()
    
    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        input_path = Path(args.file)
        output_file = input_path.parent / f"{input_path.stem}_metrics.csv"
    
    print(f"Processing {args.file}...")
    
    # Load JSON data
    with open(args.file, 'r') as f:
        data = json.load(f)
    
    # Process each question
    results = []
    for i, item in enumerate(data):
        if (i + 1) % 10 == 0:
            print(f"Processing question {i + 1}/{len(data)}...")
        
        question_id = item['question_id']
        model_outputs = item.get('model_outputs', '')
        
        # Calculate string lengths
        length_total = len(model_outputs)
        
        # Extract and measure think content
        think_content = extract_think_content(model_outputs)
        length_think = len(think_content) if think_content else 0
        
        # Tokenize full output
        tokens_total = tokenize_text(model_outputs, args.tokenize_url)
        n_tokens_total = len(tokens_total)
        
        # Tokenize think content if exists
        if think_content:
            tokens_think = tokenize_text(think_content, args.tokenize_url)
            n_tokens_think = len(tokens_think)
        else:
            n_tokens_think = 0
        
        results.append({
            'question_id': question_id,
            'length_total': length_total,
            'length_think': length_think,
            'n_tokens_total': n_tokens_total,
            'n_tokens_think': n_tokens_think,
        })
    
    # Write CSV output
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['question_id', 'length_total', 'length_think', 'n_tokens_total', 
                      'n_tokens_think']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Results written to {output_file}")
    
    # Print summary statistics
    avg_length_total = sum(r['length_total'] for r in results) / len(results)
    avg_length_think = sum(r['length_think'] for r in results) / len(results)
    avg_tokens_total = sum(r['n_tokens_total'] for r in results) / len(results)
    avg_tokens_think = sum(r['n_tokens_think'] for r in results) / len(results)
    
    print(f"\nSummary:")
    print(f"Average total length: {avg_length_total:.1f} characters")
    print(f"Average think length: {avg_length_think:.1f} characters")
    print(f"Average total tokens: {avg_tokens_total:.1f}")
    print(f"Average think tokens: {avg_tokens_think:.1f}")
    print(f"Average think/total ratio (chars): {avg_length_think/avg_length_total:.3f}")
    print(f"Average think/total ratio (tokens): {avg_tokens_think/avg_tokens_total:.3f}")


if __name__ == '__main__':
    main()
