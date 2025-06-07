#!/usr/bin/env python3
"""
Combine multiple JSON files into a single dataset with correctness and token count columns.
"""

import json
import sys
import requests
from pathlib import Path
from typing import Dict, List, Any
import argparse


def load_json_file(filepath: Path) -> List[Dict[str, Any]]:
    """Load JSON data from a file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def get_token_count(content: str, tokenize_url: str = "http://localhost:8080/tokenize") -> int:
    """Get token count from tokenization service."""
    try:
        response = requests.post(tokenize_url, json={'content': content}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return len(data.get('tokens', []))
    except Exception as e:
        print(f"Error calling tokenization service: {e}")
        return -1  # Return -1 to indicate error


def validate_question_ids(datasets: Dict[str, List[Dict[str, Any]]]) -> bool:
    """Validate that all datasets have the same set of question_ids."""
    question_id_sets = {}
    
    for filename, data in datasets.items():
        question_ids = {item['question_id'] for item in data}
        question_id_sets[filename] = question_ids
    
    # Get the first set of question_ids as reference
    reference_set = None
    reference_filename = None
    
    for filename, id_set in question_id_sets.items():
        if reference_set is None:
            reference_set = id_set
            reference_filename = filename
        else:
            if id_set != reference_set:
                print(f"Error: Question ID sets don't match!")
                print(f"{reference_filename} has {len(reference_set)} questions")
                print(f"{filename} has {len(id_set)} questions")
                
                # Show differences
                missing_in_current = reference_set - id_set
                extra_in_current = id_set - reference_set
                
                if missing_in_current:
                    print(f"Missing in {filename}: {sorted(list(missing_in_current))[:10]}...")
                if extra_in_current:
                    print(f"Extra in {filename}: {sorted(list(extra_in_current))[:10]}...")
                
                return False
    
    return True


def combine_datasets(json_files: List[str], output_file: str, tokenize_url: str):
    """Combine multiple JSON datasets into one."""
    # Load all datasets
    datasets = {}
    for filepath in json_files:
        path = Path(filepath)
        if not path.exists():
            print(f"Error: File {filepath} not found")
            sys.exit(1)
        
        filename = path.stem  # Get filename without extension
        datasets[filename] = load_json_file(path)
        print(f"Loaded {len(datasets[filename])} items from {filename}")
    
    # Validate question IDs
    if not validate_question_ids(datasets):
        print("Error: Question ID validation failed")
        sys.exit(1)
    
    print("Question ID validation passed")
    
    # Create combined dataset
    # Use the first dataset to get question_ids order
    first_filename = list(datasets.keys())[0]
    question_ids = [item['question_id'] for item in datasets[first_filename]]
    
    # Build lookup dictionaries for each dataset
    data_lookups = {}
    for filename, data in datasets.items():
        data_lookups[filename] = {item['question_id']: item for item in data}
    
    # Combine data
    combined_data = []
    
    for question_id in question_ids:
        row = {'question_id': question_id}
        
        # Add correctness and token count for each file
        for filename in sorted(datasets.keys()):
            item = data_lookups[filename][question_id]
            
            # Check correctness
            is_correct = 1 if item.get('answer') == item.get('pred') else 0
            row[f'{filename}_correct'] = is_correct
            
            # Get token count
            model_outputs = item.get('model_outputs', '')
            token_count = get_token_count(model_outputs, tokenize_url)
            row[f'{filename}_n_tokens'] = token_count
        
        combined_data.append(row)
    
    # Write output
    with open(output_file, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"\nCombined dataset written to {output_file}")
    print(f"Total rows: {len(combined_data)}")
    
    # Print column names
    if combined_data:
        columns = list(combined_data[0].keys())
        print(f"Columns ({len(columns)}): {columns}")


def main():
    parser = argparse.ArgumentParser(description='Combine JSON datasets')
    parser.add_argument('--tokenize-url', default='http://localhost:8080/tokenize',
                        help='URL of tokenization service (default: http://localhost:8080/tokenize)')
    parser.add_argument('--output', default='combined_dataset.json',
                        help='Output file path (default: combined_dataset.json)')
    args = parser.parse_args()
    
    # List of JSON files to combine
    json_files = [
        'cs_nothink.json',
        'cs_think.json',
        'cs_think_bias_19.json',
        'cs_think_bias_20.json'
    ]
    
    combine_datasets(json_files, args.output, args.tokenize_url)


if __name__ == "__main__":
    main()