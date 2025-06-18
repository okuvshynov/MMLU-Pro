#!/usr/bin/env python3
"""
Analyze differences between ML model evaluation result reports across multiple runs.
"""

import os
import json
import argparse
from collections import defaultdict
from typing import Dict, List


def load_results(directory: str, selected_runs: List[int] = None) -> Dict[str, List[tuple]]:
    """
    Load all result files from subdirectories.
    
    Args:
        directory: Path to directory containing numbered subdirectories
        selected_runs: List of run numbers to include (e.g., [0, 2]). If None, include all runs.
    
    Returns:
        Dict mapping dataset_name -> list of (run_number, run_results)
        where run_results is Dict[question_id -> result_object]
    """
    results = defaultdict(list)
    
    # Find all numbered subdirectories
    subdirs = []
    for item in os.listdir(directory):
        path = os.path.join(directory, item)
        if os.path.isdir(path) and item.isdigit():
            # Filter by selected runs if specified
            if selected_runs is None or int(item) in selected_runs:
                subdirs.append(item)
    
    subdirs.sort(key=int)
    
    # Load results from each subdirectory
    for subdir in subdirs:
        subdir_path = os.path.join(directory, subdir)
        run_number = int(subdir)
        
        # Find all *_result.json files
        for filename in os.listdir(subdir_path):
            if filename.endswith('_result.json'):
                dataset_name = filename.replace('_result.json', '')
                filepath = os.path.join(subdir_path, filename)
                
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Convert list to dict keyed by question_id
                run_results = {}
                for item in data:
                    run_results[item['question_id']] = item
                
                results[dataset_name].append((run_number, run_results))
    
    return results


def analyze_dataset(dataset_name: str, runs: List[tuple]) -> Dict:
    """
    Analyze a single dataset across multiple runs.
    
    Args:
        dataset_name: Name of the dataset
        runs: List of (run_number, run_results) tuples
    """
    num_runs = len(runs)
    
    # Get all question IDs across all runs
    all_question_ids = set()
    for run_num, run_data in runs:
        all_question_ids.update(run_data.keys())
    
    # Track correctness for each question across runs
    question_correctness = defaultdict(list)
    
    # Calculate accuracy for each run
    run_accuracies = []
    
    for run_num, run_data in runs:
        correct = 0
        total = 0
        
        for qid in all_question_ids:
            if qid in run_data:
                result = run_data[qid]
                is_correct = result.get('pred') == result.get('answer')
                question_correctness[qid].append(is_correct)
                
                if is_correct:
                    correct += 1
                total += 1
            else:
                # Question missing in this run
                question_correctness[qid].append(None)
        
        accuracy = (correct / total * 100) if total > 0 else 0
        run_accuracies.append({
            'run': run_num,  # Now using actual run number
            'correct': correct,
            'total': total,
            'accuracy': accuracy
        })
    
    # Calculate overlap metrics
    correct_in_all = 0
    correct_in_any = 0
    questions_answered = 0
    
    for qid, correctness_list in question_correctness.items():
        # Filter out None values (questions not present in some runs)
        valid_results = [c for c in correctness_list if c is not None]
        
        if valid_results:
            questions_answered += 1
            
            if all(valid_results):
                correct_in_all += 1
            
            if any(valid_results):
                correct_in_any += 1
    
    # Calculate percentages
    overlap_percentage = (correct_in_all / questions_answered * 100) if questions_answered > 0 else 0
    coverage_percentage = (correct_in_any / questions_answered * 100) if questions_answered > 0 else 0
    
    # Find questions with varying results
    varying_questions = []
    for qid, correctness_list in question_correctness.items():
        valid_results = [c for c in correctness_list if c is not None]
        if len(set(valid_results)) > 1:  # Results vary across runs
            varying_questions.append(qid)
    
    return {
        'dataset_name': dataset_name,
        'num_runs': num_runs,
        'total_questions': len(all_question_ids),
        'run_accuracies': run_accuracies,
        'overlap': {
            'correct_in_all_runs': correct_in_all,
            'percentage': overlap_percentage
        },
        'coverage': {
            'correct_in_any_run': correct_in_any,
            'percentage': coverage_percentage
        },
        'varying_questions': {
            'count': len(varying_questions),
            'question_ids': varying_questions[:10]  # Show first 10
        }
    }


def print_analysis(analysis: Dict):
    """
    Pretty print the analysis results.
    """
    print(f"\n{'='*60}")
    print(f"Dataset: {analysis['dataset_name']}")
    print(f"{'='*60}")
    print(f"Number of runs: {analysis['num_runs']}")
    print(f"Total questions: {analysis['total_questions']}")
    
    print(f"\nAccuracy per run:")
    for run_data in analysis['run_accuracies']:
        print(f"  Run {run_data['run']}: {run_data['accuracy']:.2f}% "
              f"({run_data['correct']}/{run_data['total']})")
    
    print(f"\nConsistency metrics:")
    print(f"  Overlap (correct in ALL runs): {analysis['overlap']['percentage']:.2f}% "
          f"({analysis['overlap']['correct_in_all_runs']} questions)")
    print(f"  Coverage (correct in ANY run): {analysis['coverage']['percentage']:.2f}% "
          f"({analysis['coverage']['correct_in_any_run']} questions)")
    
    print(f"\nVariability:")
    print(f"  Questions with varying results: {analysis['varying_questions']['count']}")
    if analysis['varying_questions']['question_ids']:
        print(f"  Sample question IDs: {analysis['varying_questions']['question_ids']}")
    
    # Calculate spread
    accuracies = [r['accuracy'] for r in analysis['run_accuracies']]
    if len(accuracies) > 1:
        spread = max(accuracies) - min(accuracies)
        print(f"  Accuracy spread: {spread:.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze differences between ML model evaluation runs'
    )
    parser.add_argument(
        'directory',
        help='Path to directory containing numbered subdirectories with results'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    parser.add_argument(
        '--runs',
        type=str,
        help='Comma-separated list of run numbers to include (e.g., "0,2")'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        return 1
    
    # Parse selected runs
    selected_runs = None
    if args.runs:
        try:
            selected_runs = [int(x.strip()) for x in args.runs.split(',')]
            print(f"Selecting runs: {selected_runs}")
        except ValueError:
            print(f"Error: Invalid run numbers '{args.runs}'. Use comma-separated integers.")
            return 1
    
    # Load results
    print(f"Loading results from: {args.directory}")
    results = load_results(args.directory, selected_runs)
    
    if not results:
        print("No result files found!")
        return 1
    
    # Analyze each dataset
    all_analyses = {}
    
    for dataset_name, runs in results.items():
        if len(runs) < 2:
            print(f"Warning: Dataset '{dataset_name}' has only {len(runs)} run(s). Need at least 2 runs for comparison.")
            continue
        
        analysis = analyze_dataset(dataset_name, runs)
        all_analyses[dataset_name] = analysis
        
        if not args.json:
            print_analysis(analysis)
    
    if args.json:
        print(json.dumps(all_analyses, indent=2))
    
    return 0


if __name__ == '__main__':
    exit(main())