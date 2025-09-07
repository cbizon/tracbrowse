#!/usr/bin/env python3
"""
Script to find top N highest scoring rows from a CSV file using a priority queue.
"""
import heapq
import csv
import argparse
import sys

def get_top_n_scores(filename, n):
    """
    Read CSV file and return top N rows with highest TracInScore values.
    Uses a min-heap to efficiently maintain only the top N scores.
    """
    # Use min-heap to keep track of top N scores
    # We store negative scores to simulate max-heap behavior
    top_scores = []
    row_counter = 0
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    score = float(row['TracInScore'])
                    row_counter += 1
                    
                    # If we have less than n items, just add
                    if len(top_scores) < n:
                        heapq.heappush(top_scores, (score, row_counter, dict(row)))
                    else:
                        # If current score is higher than lowest in heap, replace
                        if score > top_scores[0][0]:
                            heapq.heapreplace(top_scores, (score, row_counter, dict(row)))
                            
                except ValueError:
                    # Skip rows with invalid scores
                    continue
                    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Sort by score descending (highest first)
    top_scores.sort(key=lambda x: x[0], reverse=True)
    
    return [row for score, counter, row in top_scores]

def write_results(rows, output_filename=None):
    """Write results to file or stdout."""
    if not rows:
        print("No valid rows found.")
        return
    
    fieldnames = rows[0].keys()
    
    if output_filename:
        with open(output_filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Results written to {output_filename}")
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser(
        description='Find top N highest scoring rows from CSV file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Process default input file to get top 100000 scores
  python src/top_scores.py 100000
  
  # Process specific file
  python src/top_scores.py input_data/myfile.csv 50000
  
  # Specify custom output location
  python src/top_scores.py 100000 -o filtered_data/custom_output.csv
        '''
    )
    parser.add_argument('filename_or_n', help='Input CSV filename or number of top scores (if using default input)')
    parser.add_argument('n', nargs='?', type=int, help='Number of top scores to return (required if first arg is filename)')
    parser.add_argument('-o', '--output', help='Output filename (default: filtered_data/top_N_results.csv)')
    
    args = parser.parse_args()
    
    # Determine if first argument is filename or number
    try:
        # Try to parse first argument as integer
        n = int(args.filename_or_n)
        filename = None
        if args.n is not None:
            print("Error: When providing N as first argument, don't provide it again as second argument.")
            sys.exit(1)
    except ValueError:
        # First argument is filename
        filename = args.filename_or_n
        n = args.n
        if n is None:
            print("Error: When providing filename, you must also provide N (number of top scores).")
            sys.exit(1)
    
    if n <= 0:
        print("Error: N must be a positive integer.")
        sys.exit(1)
    
    # Set default input file if none provided
    if filename is None:
        filename = 'input_data/influencescores_testtreatsedge1.csv'
        print(f"Using default input file: {filename}")
    
    # Set default output file if none provided
    output_filename = args.output
    if output_filename is None:
        import os
        os.makedirs('filtered_data', exist_ok=True)
        output_filename = f'filtered_data/top_{n}_results.csv'
    
    print(f"Finding top {n} scores from {filename}...")
    print(f"Output will be written to: {output_filename}")
    
    top_rows = get_top_n_scores(filename, n)
    
    if top_rows:
        print(f"Found {len(top_rows)} top scoring rows.")
        write_results(top_rows, output_filename)
        print(f"✅ Processing complete! Output saved to: {output_filename}")
    else:
        print("No valid scores found in the file.")

if __name__ == "__main__":
    main()