import json
import sys
from collections import defaultdict

def identify_shorter_runs(json_data_string):
    try:
        data = json.loads(json_data_string)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}", file=sys.stderr)
        return []

    # Group by date
    runs_by_date = defaultdict(list)
    for run_info in data:
        runs_by_date[run_info['date']].append(run_info)

    files_to_move = []
    for date, runs in runs_by_date.items():
        if len(runs) > 1:  # Only consider dates with multiple runs
            # Find the run with the maximum distance for this date
            longest_run = max(runs, key=lambda x: x['distance'])
            
            # Identify shorter runs
            for run_info in runs:
                if run_info['filepath'] != longest_run['filepath']:
                    year = run_info['date'][:4] # Extract year from YYYY-MM-DD
                    files_to_move.append({
                        'filepath': run_info['filepath'],
                        'year': year
                    })
    return files_to_move

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_input_string = sys.argv[1]
    else:
        # Attempt to read from stdin if no argument is provided
        # This might be more robust if the string is very long
        json_input_string = sys.stdin.read()

    if not json_input_string:
        print("No JSON input provided.", file=sys.stderr)
        sys.exit(1)

    shorter_runs = identify_shorter_runs(json_input_string)
    print(json.dumps(shorter_runs, indent=2))
