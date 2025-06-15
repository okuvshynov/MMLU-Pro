#!/usr/bin/env python3
"""
Pretty print a question entry from all available JSON files.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import textwrap


def load_json_file(filepath: Path) -> list:
    """Load JSON data from a file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def find_question_by_id(data: list, question_id: int) -> Optional[Dict[str, Any]]:
    """Find a question entry by its ID."""
    for item in data:
        if item.get('question_id') == question_id:
            return item
    return None


def format_options(options: list) -> str:
    """Format multiple choice options nicely."""
    formatted = []
    for i, opt in enumerate(options):
        letter = chr(65 + i)  # A, B, C, etc.
        formatted.append(f"   {letter}. {opt}")
    return '\n'.join(formatted)


def print_question_entry(filename: str, entry: Dict[str, Any], show_model_output: bool = True):
    """Pretty print a question entry."""
    print(f"\n{'='*80}")
    print(f"FILE: {filename}")
    print('='*80)
    
    if entry is None:
        print("  [Question not found in this file]")
        return
    
    # Basic information
    print(f"Question ID: {entry.get('question_id', 'N/A')}")
    print(f"Category: {entry.get('category', 'N/A')}")
    print(f"Source: {entry.get('src', 'N/A')}")
    
    # Question text
    print(f"\nQuestion:")
    question_text = entry.get('question', 'N/A')
    wrapped = textwrap.fill(question_text, width=76, initial_indent='  ', subsequent_indent='  ')
    print(wrapped)
    
    # Options
    if 'options' in entry:
        print(f"\nOptions:")
        print(format_options(entry['options']))
    
    # Answer and prediction
    answer = entry.get('answer', 'N/A')
    answer_index = entry.get('answer_index', 'N/A')
    pred = entry.get('pred', 'N/A')
    
    print(f"\nCorrect Answer: {answer} (index: {answer_index})")
    if 'options' in entry and isinstance(answer_index, int) and 0 <= answer_index < len(entry['options']):
        print(f"  → {entry['options'][answer_index]}")
    
    print(f"\nModel Prediction: {pred}")
    if pred != answer:
        print("  ❌ INCORRECT")
    else:
        print("  ✓ CORRECT")
    
    # Model outputs
    if show_model_output and 'model_outputs' in entry:
        print(f"\nModel Output:")
        output = entry.get('model_outputs', '')
        
        # Try to format the output nicely
        if output:
            # Split by line and wrap each line
            lines = output.split('\n')
            for line in lines:
                if line.strip():
                    wrapped = textwrap.fill(line, width=76, initial_indent='  ', subsequent_indent='  ')
                    print(wrapped)
                else:
                    print()
        else:
            print("  [No output]")
    
    # COT content if available
    if 'cot_content' in entry and entry['cot_content']:
        print(f"\nCOT Content:")
        cot = entry.get('cot_content', '')
        wrapped = textwrap.fill(cot, width=76, initial_indent='  ', subsequent_indent='  ')
        print(wrapped)


def main():
    parser = argparse.ArgumentParser(description='Inspect a specific question across all JSON files')
    parser.add_argument('question_id', type=int, help='Question ID to inspect')
    parser.add_argument('--no-output', action='store_true', 
                        help='Hide model outputs for brevity')
    parser.add_argument('--files', nargs='+', 
                        default=None,
                        help='JSON files to inspect (default: auto-detect all available files)')
    
    args = parser.parse_args()
    
    # Auto-detect files if not specified
    if args.files is None:
        json_files = ['cs_nothink.json', 'cs_think.json']
        
        # Find all cs_think_bias_*.json files
        bias_files = sorted(Path('.').glob('cs_think_bias_*.json'))
        json_files.extend([str(f) for f in bias_files])
        
        args.files = json_files
        print(f"\nAuto-detected {len(args.files)} JSON files:")
        for f in args.files:
            print(f"  - {f}")
    
    print(f"\nSearching for Question ID: {args.question_id}")
    
    found_any = False
    
    for filename in args.files:
        filepath = Path(filename)
        if not filepath.exists():
            print(f"\n[Warning: File {filename} not found, skipping]")
            continue
        
        # Load data
        data = load_json_file(filepath)
        
        # Find question
        entry = find_question_by_id(data, args.question_id)
        
        if entry:
            found_any = True
            print_question_entry(filename, entry, show_model_output=not args.no_output)
        else:
            print(f"\n[Question ID {args.question_id} not found in {filename}]")
    
    if not found_any:
        print(f"\n❌ Question ID {args.question_id} was not found in any file.")
    else:
        print(f"\n{'='*80}")
        print("Summary comparison complete.")
        
        # Quick comparison if all files were checked
        if len(args.files) >= 2:
            print("\nQuick Answer Comparison:")
            for filename in args.files:
                filepath = Path(filename)
                if filepath.exists():
                    data = load_json_file(filepath)
                    entry = find_question_by_id(data, args.question_id)
                    if entry:
                        answer = entry.get('answer', '?')
                        pred = entry.get('pred', '?')
                        status = "✓" if answer == pred else "❌"
                        print(f"  {filename:<25} Answer: {answer} → Pred: {pred} {status}")


if __name__ == "__main__":
    main()