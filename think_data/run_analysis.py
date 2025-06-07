#!/usr/bin/env python3
"""
Run the complete analysis pipeline:
1. Combine datasets
2. Summarize the combined dataset
3. Run simulations with different probabilities
4. Create visualization
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running {description}:")
        print(result.stderr)
        return False
    
    print(result.stdout)
    return True


def main():
    # Check if tokenization service URL is provided
    tokenize_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/tokenize"
    
    print(f"Using tokenization service at: {tokenize_url}")
    print("\nNOTE: Make sure the tokenization service is running!")
    input("Press Enter to continue...")
    
    # Step 1: Combine datasets
    if not Path('combined_dataset.json').exists():
        if not run_command(
            ['python', 'combine_datasets.py', '--tokenize-url', tokenize_url],
            "Combining datasets"
        ):
            print("Failed to combine datasets. Exiting.")
            return
    else:
        print("\nCombined dataset already exists, skipping...")
    
    # Step 2: Summarize
    if not run_command(
        ['python', 'summarize.py', '--output', 'summary.json'],
        "Creating summary"
    ):
        print("Warning: Failed to create summary, continuing...")
    
    # Step 3: Run simulations with different probabilities
    probabilities = [0.0, 0.25, 0.5, 0.75, 1.0]
    
    for p in probabilities:
        output_file = f"simulation_results_p{p}_n1000.json"
        if not Path(output_file).exists():
            if not run_command(
                ['python', 'simulate_selection.py', '-p', str(p), '-n', '1000', '--seed', '42'],
                f"Running simulation with p={p}"
            ):
                print(f"Warning: Failed simulation for p={p}, continuing...")
        else:
            print(f"\nSimulation results for p={p} already exist, skipping...")
    
    # Step 4: Create visualization
    if not run_command(
        ['python', 'visualize_accuracy_tokens.py'],
        "Creating visualization"
    ):
        print("Failed to create visualization.")
        return
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)
    print("\nGenerated files:")
    print("- combined_dataset.json: Combined dataset with all metrics")
    print("- summary.json: Summary statistics")
    print("- simulation_results_p*.json: Simulation results for different probabilities")
    print("- accuracy_vs_tokens_scatter.png/pdf: Visualization")


if __name__ == "__main__":
    main()