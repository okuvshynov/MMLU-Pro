#!/usr/bin/env python3
"""
Compare token metrics between two CSV files and plot the differences.
"""

import pandas as pd
import matplotlib.pyplot as plt
import argparse
import sys
from pathlib import Path


def load_and_merge_data(file_a, file_b):
    """Load two CSV files and merge them on question_id."""
    try:
        df_a = pd.read_csv(file_a)
        df_b = pd.read_csv(file_b)
    except Exception as e:
        print(f"Error reading CSV files: {e}")
        sys.exit(1)
    
    # Merge dataframes on question_id
    merged_df = pd.merge(
        df_a, 
        df_b, 
        on='question_id', 
        suffixes=('_a', '_b'),
        how='inner'
    )
    
    if merged_df.empty:
        print("No matching question_ids found between the two files.")
        sys.exit(1)
    
    return merged_df


def calculate_differences(merged_df):
    """Calculate token differences between files A and B."""
    # Calculate differences (file_a - file_b)
    merged_df['n_tokens_think_diff'] = merged_df['n_tokens_think_a'] - merged_df['n_tokens_think_b']
    merged_df['n_tokens_total_diff'] = merged_df['n_tokens_total_a'] - merged_df['n_tokens_total_b']
    
    return merged_df


def plot_distributions(df, output_prefix):
    """Plot distributions of token differences and save to PNG files."""
    # Set style for better-looking plots
    plt.style.use('seaborn-v0_8')
    
    # Plot 1: Distribution of n_tokens_think differences
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    ax1.hist(df['n_tokens_think_diff'], bins=30, edgecolor='black', alpha=0.7)
    ax1.set_xlabel('Difference in n_tokens_think (File A - File B)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of Thinking Token Differences')
    ax1.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='Zero difference')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Add statistics
    mean_diff = df['n_tokens_think_diff'].mean()
    median_diff = df['n_tokens_think_diff'].median()
    ax1.text(0.02, 0.98, f'Mean: {mean_diff:.2f}\nMedian: {median_diff:.2f}',
             transform=ax1.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_think_tokens_diff.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Plot 2: Distribution of n_tokens_total differences
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.hist(df['n_tokens_total_diff'], bins=30, edgecolor='black', alpha=0.7, color='green')
    ax2.set_xlabel('Difference in n_tokens_total (File A - File B)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution of Total Token Differences')
    ax2.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='Zero difference')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Add statistics
    mean_diff = df['n_tokens_total_diff'].mean()
    median_diff = df['n_tokens_total_diff'].median()
    ax2.text(0.02, 0.98, f'Mean: {mean_diff:.2f}\nMedian: {median_diff:.2f}',
             transform=ax2.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_total_tokens_diff.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Plot 3: Scatter plot showing relationship between think and total token differences
    fig3, ax3 = plt.subplots(figsize=(10, 8))
    scatter = ax3.scatter(df['n_tokens_think_diff'], df['n_tokens_total_diff'], 
                         alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
    ax3.set_xlabel('Difference in n_tokens_think (File A - File B)')
    ax3.set_ylabel('Difference in n_tokens_total (File A - File B)')
    ax3.set_title('Relationship between Think and Total Token Differences')
    ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax3.axvline(x=0, color='red', linestyle='--', alpha=0.5)
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_scatter_diff.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nPlots saved:")
    print(f"  - {output_prefix}_think_tokens_diff.png")
    print(f"  - {output_prefix}_total_tokens_diff.png")
    print(f"  - {output_prefix}_scatter_diff.png")


def main():
    parser = argparse.ArgumentParser(description='Compare token metrics between two CSV files')
    parser.add_argument('file_a', help='Path to first CSV file')
    parser.add_argument('file_b', help='Path to second CSV file')
    parser.add_argument('-o', '--output-prefix', default='token_comparison',
                       help='Prefix for output PNG files (default: token_comparison)')
    
    args = parser.parse_args()
    
    # Verify files exist
    if not Path(args.file_a).exists():
        print(f"Error: File '{args.file_a}' does not exist")
        sys.exit(1)
    if not Path(args.file_b).exists():
        print(f"Error: File '{args.file_b}' does not exist")
        sys.exit(1)
    
    print(f"Comparing token metrics between:")
    print(f"  File A: {args.file_a}")
    print(f"  File B: {args.file_b}")
    
    # Load and process data
    merged_df = load_and_merge_data(args.file_a, args.file_b)
    print(f"\nFound {len(merged_df)} matching questions")
    
    # Calculate differences
    df_with_diffs = calculate_differences(merged_df)
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"n_tokens_think differences:")
    print(f"  Mean: {df_with_diffs['n_tokens_think_diff'].mean():.2f}")
    print(f"  Median: {df_with_diffs['n_tokens_think_diff'].median():.2f}")
    print(f"  Std Dev: {df_with_diffs['n_tokens_think_diff'].std():.2f}")
    print(f"  Min: {df_with_diffs['n_tokens_think_diff'].min()}")
    print(f"  Max: {df_with_diffs['n_tokens_think_diff'].max()}")
    
    print(f"\nn_tokens_total differences:")
    print(f"  Mean: {df_with_diffs['n_tokens_total_diff'].mean():.2f}")
    print(f"  Median: {df_with_diffs['n_tokens_total_diff'].median():.2f}")
    print(f"  Std Dev: {df_with_diffs['n_tokens_total_diff'].std():.2f}")
    print(f"  Min: {df_with_diffs['n_tokens_total_diff'].min()}")
    print(f"  Max: {df_with_diffs['n_tokens_total_diff'].max()}")
    
    # Plot distributions
    plot_distributions(df_with_diffs, args.output_prefix)


if __name__ == '__main__':
    main()