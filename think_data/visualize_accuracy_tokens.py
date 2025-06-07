#!/usr/bin/env python3
"""
Create a scatter plot of accuracy vs token count for real and simulated data.
"""

import json
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Tuple


def load_combined_dataset(filepath: Path) -> List[Dict[str, Any]]:
    """Load combined dataset."""
    with open(filepath, 'r') as f:
        return json.load(f)


def calculate_dataset_stats(data: List[Dict[str, Any]], column_prefix: str) -> Tuple[float, int]:
    """Calculate accuracy and total tokens for a specific dataset column."""
    correct_col = f"{column_prefix}_correct"
    tokens_col = f"{column_prefix}_n_tokens"
    
    total_correct = sum(row.get(correct_col, 0) for row in data)
    total_tokens = sum(row.get(tokens_col, 0) for row in data)
    total_questions = len(data)
    
    accuracy = total_correct / total_questions if total_questions > 0 else 0
    
    return accuracy, total_tokens


def load_simulation_results(pattern: str) -> List[Dict[str, float]]:
    """Load simulation results from JSON files."""
    results = []
    
    # Find all simulation result files
    for filepath in Path('.').glob(pattern):
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Extract individual simulation results
        for result in data.get('all_results', []):
            results.append({
                'accuracy': result['accuracy'],
                'total_tokens': result['total_tokens'],
                'probability': data['parameters']['probability']
            })
    
    return results


def create_scatter_plot(combined_file: str, simulation_pattern: str = "simulation_results_*.json"):
    """Create scatter plot of accuracy vs tokens."""
    
    # Load combined dataset
    print(f"Loading combined dataset from {combined_file}...")
    data = load_combined_dataset(Path(combined_file))
    
    # Define colors and markers
    colors = {
        'cs_nothink': '#FF6B6B',      # Red
        'cs_think': '#4ECDC4',         # Teal
        'cs_think_bias': '#FFD93D',    # Yellow/Gold
        'simulation': '#95E1D3'        # Light teal
    }
    
    markers = {
        'cs_nothink': 'o',
        'cs_think': 's',
        'cs_think_bias_19': '.',
        'cs_think_bias_20': '.',
        'simulation': '.'
    }
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot real datasets
    datasets = ['cs_nothink', 'cs_think', 'cs_think_bias_19', 'cs_think_bias_20']
    
    for dataset in datasets:
        try:
            accuracy, total_tokens = calculate_dataset_stats(data, dataset)
            
            # Determine color
            if 'bias' in dataset:
                color = colors['cs_think_bias']
            else:
                color = colors.get(dataset, 'gray')
            
            # Determine marker
            marker = markers.get(dataset, 'o')
            
            # Determine size based on dataset type
            if 'bias' in dataset:
                size = 100  # Smaller size for bias datasets
                edge_color = 'none'
                linewidth = 0
            else:
                size = 200  # Larger size for main datasets
                edge_color = 'black'
                linewidth = 1.5
            
            # Plot with appropriate size
            ax.scatter(total_tokens, accuracy, 
                      color=color, 
                      marker=marker, 
                      s=size,
                      edgecolors=edge_color,
                      linewidth=linewidth,
                      label=dataset,
                      zorder=3)  # Plot on top
            
            print(f"{dataset}: accuracy={accuracy:.4f}, tokens={total_tokens}")
            
        except Exception as e:
            print(f"Warning: Could not process {dataset}: {e}")
    
    # Load and plot simulation results
    print(f"\nLoading simulation results...")
    sim_results = load_simulation_results(simulation_pattern)
    
    if sim_results:
        sim_tokens = [r['total_tokens'] for r in sim_results]
        sim_accuracy = [r['accuracy'] for r in sim_results]
        
        # Group by probability for different transparencies
        probs = list(set(r['probability'] for r in sim_results))
        
        for prob in sorted(probs):
            prob_results = [r for r in sim_results if r['probability'] == prob]
            prob_tokens = [r['total_tokens'] for r in prob_results]
            prob_accuracy = [r['accuracy'] for r in prob_results]
            
            ax.scatter(prob_tokens, prob_accuracy,
                      color=colors['simulation'],
                      marker=markers['simulation'],
                      s=30,
                      alpha=0.3,
                      label=f'simulation (p={prob})',
                      zorder=1)
        
        print(f"Plotted {len(sim_results)} simulation results")
    
    # Add theoretical mixing lines
    if 'cs_think' in datasets and 'cs_nothink' in datasets:
        think_acc, think_tokens = calculate_dataset_stats(data, 'cs_think')
        nothink_acc, nothink_tokens = calculate_dataset_stats(data, 'cs_nothink')
        
        # Create mixing line
        p_values = np.linspace(0, 1, 11)
        mix_tokens = []
        mix_accuracy = []
        
        for p in p_values:
            mix_acc = p * think_acc + (1 - p) * nothink_acc
            mix_tok = p * think_tokens + (1 - p) * nothink_tokens
            mix_accuracy.append(mix_acc)
            mix_tokens.append(mix_tok)
        
        ax.plot(mix_tokens, mix_accuracy, 'k--', alpha=0.5, 
                label='Theoretical mixing', linewidth=2, zorder=2)
        
        # Add probability labels on the mixing line
        for i, p in enumerate([0.0, 0.25, 0.5, 0.75, 1.0]):
            idx = int(p * 10)
            ax.annotate(f'p={p}', 
                       xy=(mix_tokens[idx], mix_accuracy[idx]),
                       xytext=(5, 5), 
                       textcoords='offset points',
                       fontsize=8,
                       alpha=0.7)
    
    # Formatting
    ax.set_xlabel('Total Tokens', fontsize=14)
    ax.set_ylabel('Accuracy', fontsize=14)
    ax.set_title('Accuracy vs Token Usage: Real and Simulated Data', fontsize=16)
    
    # Set y-axis limits to [0, 1]
    ax.set_ylim(0, 1)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Create custom legend
    handles, labels = ax.get_legend_handles_labels()
    
    # Group legend items
    real_handles = []
    real_labels = []
    sim_handles = []
    sim_labels = []
    other_handles = []
    other_labels = []
    
    for h, l in zip(handles, labels):
        if 'simulation' in l:
            if l not in sim_labels:  # Avoid duplicates
                sim_handles.append(h)
                sim_labels.append(l)
        elif l == 'Theoretical mixing':
            other_handles.append(h)
            other_labels.append(l)
        else:
            real_handles.append(h)
            real_labels.append(l)
    
    # Combine for legend
    all_handles = real_handles + sim_handles + other_handles
    all_labels = real_labels + sim_labels + other_labels
    
    ax.legend(all_handles, all_labels, 
              loc='best', 
              framealpha=0.9,
              ncol=2 if len(all_labels) > 6 else 1)
    
    # Save plot
    output_file = 'accuracy_vs_tokens_scatter.png'
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to {output_file}")
    
    # Also save as PDF for better quality
    plt.savefig('accuracy_vs_tokens_scatter.pdf', bbox_inches='tight')
    print(f"Plot also saved as PDF")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Visualize accuracy vs token usage')
    parser.add_argument('--input', '-i', default='combined_dataset.json',
                        help='Path to combined dataset (default: combined_dataset.json)')
    parser.add_argument('--simulations', '-s', default='simulation_results_*.json',
                        help='Pattern for simulation result files (default: simulation_results_*.json)')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found")
        print("Please run combine_datasets.py first to create the combined dataset")
        return
    
    create_scatter_plot(args.input, args.simulations)


if __name__ == "__main__":
    main()