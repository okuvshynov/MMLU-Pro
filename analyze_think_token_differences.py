#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

def analyze_think_token_differences(csv_file1, csv_file2):
    """
    Analyze differences in n_tokens_think field between two CSV files.
    
    Returns counts for:
    1) Same values (including both = 0)
    2) Different values, both non-zero
    3) One value is 0, the other is non-zero
    """
    # Read first CSV file
    data1 = {}
    with open(csv_file1, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            question_id = row['question_id']
            n_tokens_think = int(row['n_tokens_think'])
            data1[question_id] = n_tokens_think
    
    # Read second CSV file and compare
    same_values = 0
    different_both_nonzero = 0
    one_is_zero = 0
    missing_in_first = 0
    missing_in_second = []
    
    with open(csv_file2, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            question_id = row['question_id']
            n_tokens_think2 = int(row['n_tokens_think'])
            
            if question_id in data1:
                n_tokens_think1 = data1[question_id]
                
                if n_tokens_think1 == n_tokens_think2:
                    same_values += 1
                elif n_tokens_think1 == 0 or n_tokens_think2 == 0:
                    one_is_zero += 1
                else:
                    different_both_nonzero += 1
                
                # Mark as processed
                data1[question_id] = None
            else:
                missing_in_first += 1
    
    # Check for questions in first file but not in second
    for question_id, value in data1.items():
        if value is not None:
            missing_in_second.append(question_id)
    
    return {
        'same_values': same_values,
        'different_both_nonzero': different_both_nonzero,
        'one_is_zero': one_is_zero,
        'missing_in_first': missing_in_first,
        'missing_in_second': len(missing_in_second),
        'total_compared': same_values + different_both_nonzero + one_is_zero
    }

def main():
    if len(sys.argv) != 3:
        print("Usage: python analyze_think_token_differences.py <csv_file1> <csv_file2>")
        sys.exit(1)
    
    csv_file1 = Path(sys.argv[1])
    csv_file2 = Path(sys.argv[2])
    
    if not csv_file1.exists():
        print(f"Error: File {csv_file1} does not exist")
        sys.exit(1)
    
    if not csv_file2.exists():
        print(f"Error: File {csv_file2} does not exist")
        sys.exit(1)
    
    print(f"Analyzing differences between:")
    print(f"  File 1: {csv_file1}")
    print(f"  File 2: {csv_file2}")
    print()
    
    results = analyze_think_token_differences(csv_file1, csv_file2)
    
    print("Results:")
    print(f"1) Same values (including both = 0): {results['same_values']}")
    print(f"2) Different values, both non-zero: {results['different_both_nonzero']}")
    print(f"3) One value is 0, other is non-zero: {results['one_is_zero']}")
    print()
    print(f"Total questions compared: {results['total_compared']}")
    
    if results['missing_in_first'] > 0:
        print(f"Questions in file 2 but not in file 1: {results['missing_in_first']}")
    if results['missing_in_second'] > 0:
        print(f"Questions in file 1 but not in file 2: {results['missing_in_second']}")

if __name__ == "__main__":
    main()