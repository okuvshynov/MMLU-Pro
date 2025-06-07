#!/usr/bin/env python3
"""
Simulate random selection between cs_think and cs_nothink datasets using combined dataset.
"""

import json
import random
import argparse
from pathlib import Path
from typing import Dict, List, Any
import numpy as np


def load_combined_dataset(filepath: Path) -> List[Dict[str, Any]]:
    """Load combined dataset."""
    with open(filepath, 'r') as f:
        return json.load(f)


def simulate_selection_from_combined(data: List[Dict[str, Any]], 
                                   probability: float) -> Dict[str, Any]:
    """
    Simulate selection between think and nothink columns in combined dataset.
    With probability p, select from cs_think; with (1-p), select from cs_nothink.
    Returns summary statistics.
    """
    correct_count = 0
    total_count = 0
    total_tokens = 0
    
    for row in data:
        # Randomly decide which dataset to use
        use_think = random.random() < probability
        
        if use_think:
            correct = row.get('cs_think_correct', 0)
            tokens = row.get('cs_think_n_tokens', 0)
        else:
            correct = row.get('cs_nothink_correct', 0)
            tokens = row.get('cs_nothink_n_tokens', 0)
        
        correct_count += correct
        total_tokens += tokens
        total_count += 1
    
    accuracy = correct_count / total_count if total_count > 0 else 0
    avg_tokens = total_tokens / total_count if total_count > 0 else 0
    
    return {
        'correct': correct_count,
        'total': total_count,
        'accuracy': accuracy,
        'total_tokens': total_tokens,
        'avg_tokens': avg_tokens
    }


def run_simulations(combined_file: str, probability: float, num_repeats: int) -> None:
    """Run multiple simulations and print summary statistics."""
    
    # Load combined dataset
    print(f"Loading combined dataset from {combined_file}...")
    data = load_combined_dataset(Path(combined_file))
    
    if not data:
        print("Error: Dataset is empty")
        return
    
    print(f"Dataset loaded successfully. Total questions: {len(data)}")
    
    # Check if required columns exist
    first_row = data[0]
    required_cols = ['cs_think_correct', 'cs_nothink_correct', 'cs_think_n_tokens', 'cs_nothink_n_tokens']
    missing_cols = [col for col in required_cols if col not in first_row]
    
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        print(f"Available columns: {list(first_row.keys())}")
        return
    
    print(f"\nRunning {num_repeats} simulations with p={probability}")
    print(f"(p={probability} for cs_think, p={1-probability} for cs_nothink)")
    
    # Run simulations
    results = []
    
    for i in range(num_repeats):
        result = simulate_selection_from_combined(data, probability)
        results.append(result)
        
        if (i + 1) % 100 == 0:
            print(f"  Completed {i + 1} simulations...")
    
    # Calculate summary statistics
    accuracies = [r['accuracy'] for r in results]
    correct_counts = [r['correct'] for r in results]
    total_tokens = [r['total_tokens'] for r in results]
    avg_tokens = [r['avg_tokens'] for r in results]
    
    print("\n" + "="*50)
    print("SIMULATION RESULTS")
    print("="*50)
    print(f"Probability of selecting cs_think: {probability}")
    print(f"Number of simulations: {num_repeats}")
    print(f"Questions per simulation: {results[0]['total']}")
    
    print(f"\nAccuracy Statistics:")
    print(f"  Mean accuracy: {np.mean(accuracies):.4f} ({np.mean(accuracies)*100:.2f}%)")
    print(f"  Std deviation: {np.std(accuracies):.4f}")
    print(f"  Min accuracy: {np.min(accuracies):.4f} ({np.min(accuracies)*100:.2f}%)")
    print(f"  Max accuracy: {np.max(accuracies):.4f} ({np.max(accuracies)*100:.2f}%)")
    
    print(f"\nCorrect Answers Statistics:")
    print(f"  Mean correct: {np.mean(correct_counts):.2f}")
    print(f"  Std deviation: {np.std(correct_counts):.2f}")
    print(f"  Min correct: {np.min(correct_counts)}")
    print(f"  Max correct: {np.max(correct_counts)}")
    
    print(f"\nToken Statistics:")
    print(f"  Mean total tokens: {np.mean(total_tokens):.2f}")
    print(f"  Std deviation: {np.std(total_tokens):.2f}")
    print(f"  Min total tokens: {np.min(total_tokens)}")
    print(f"  Max total tokens: {np.max(total_tokens)}")
    print(f"  Mean avg tokens per response: {np.mean(avg_tokens):.2f}")
    
    # Calculate percentiles
    percentiles = [5, 25, 50, 75, 95]
    print(f"\nAccuracy Percentiles:")
    for p in percentiles:
        value = np.percentile(accuracies, p)
        print(f"  {p}th percentile: {value:.4f} ({value*100:.2f}%)")
    
    print(f"\nToken Usage Percentiles:")
    for p in percentiles:
        value = np.percentile(total_tokens, p)
        print(f"  {p}th percentile: {value:.0f} tokens")
    
    # Calculate baseline accuracies for comparison
    think_correct = sum(row.get('cs_think_correct', 0) for row in data)
    nothink_correct = sum(row.get('cs_nothink_correct', 0) for row in data)
    total_questions = len(data)
    
    think_accuracy = think_correct / total_questions if total_questions > 0 else 0
    nothink_accuracy = nothink_correct / total_questions if total_questions > 0 else 0
    
    print(f"\nBaseline Accuracies:")
    print(f"  cs_think only: {think_accuracy:.4f} ({think_accuracy*100:.2f}%)")
    print(f"  cs_nothink only: {nothink_accuracy:.4f} ({nothink_accuracy*100:.2f}%)")
    print(f"  Expected (weighted): {probability * think_accuracy + (1-probability) * nothink_accuracy:.4f}")
    
    # Save detailed results if needed
    output_file = f"simulation_results_p{probability}_n{num_repeats}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'parameters': {
                'probability': probability,
                'num_repeats': num_repeats,
                'combined_file': combined_file
            },
            'summary': {
                'mean_accuracy': float(np.mean(accuracies)),
                'std_accuracy': float(np.std(accuracies)),
                'min_accuracy': float(np.min(accuracies)),
                'max_accuracy': float(np.max(accuracies)),
                'mean_tokens': float(np.mean(total_tokens)),
                'std_tokens': float(np.std(total_tokens)),
                'percentiles': {
                    'accuracy': {str(p): float(np.percentile(accuracies, p)) for p in percentiles},
                    'tokens': {str(p): float(np.percentile(total_tokens, p)) for p in percentiles}
                }
            },
            'baselines': {
                'cs_think_accuracy': think_accuracy,
                'cs_nothink_accuracy': nothink_accuracy,
                'expected_accuracy': probability * think_accuracy + (1-probability) * nothink_accuracy
            },
            'all_results': results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Simulate random selection using combined dataset')
    parser.add_argument('--probability', '-p', type=float, default=0.5,
                        help='Probability of selecting from cs_think (default: 0.5)')
    parser.add_argument('--repeats', '-n', type=int, default=1000,
                        help='Number of simulation repeats (default: 1000)')
    parser.add_argument('--input', '-i', default='combined_dataset.json',
                        help='Path to combined dataset (default: combined_dataset.json)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility (optional)')
    
    args = parser.parse_args()
    
    # Validate probability
    if not 0 <= args.probability <= 1:
        print("Error: Probability must be between 0 and 1")
        return
    
    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
        print(f"Random seed set to: {args.seed}")
    
    # Check if file exists
    if not Path(args.input).exists():
        print(f"Error: File '{args.input}' not found")
        print("Please run combine_datasets.py first to create the combined dataset")
        return
    
    # Run simulations
    run_simulations(args.input, args.probability, args.repeats)


if __name__ == "__main__":
    main()