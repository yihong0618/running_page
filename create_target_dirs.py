import json
import sys
import os

def create_directories_for_moving(json_data_string):
    try:
        files_to_move = json.loads(json_data_string)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}", file=sys.stderr)
        return

    if not files_to_move:
        print("No files to process.", file=sys.stderr)
        return

    base_target_dir = "/app/dual_date"

    # Create the main /app/dual_date directory
    try:
        os.makedirs(base_target_dir, exist_ok=True)
        print(f"Base directory '{base_target_dir}' ensured.")
    except OSError as e:
        print(f"Error creating base directory {base_target_dir}: {e}", file=sys.stderr)
        return

    # Extract unique years
    unique_years = set()
    for item in files_to_move:
        if 'year' in item:
            unique_years.add(item['year'])
        else:
            print(f"Warning: Item {item.get('filepath', 'Unknown file')} missing 'year'.", file=sys.stderr)


    if not unique_years:
        print("No years found in the input data to create subdirectories.", file=sys.stderr)
        return

    # Create year-specific subdirectories
    for year in unique_years:
        year_dir = os.path.join(base_target_dir, str(year))
        try:
            os.makedirs(year_dir, exist_ok=True)
            print(f"Ensured directory: {year_dir}")
        except OSError as e:
            print(f"Error creating directory {year_dir}: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_input_string = sys.argv[1]
    else:
        json_input_string = sys.stdin.read()

    if not json_input_string.strip():
        print("No JSON input provided.", file=sys.stderr)
        sys.exit(1)
    
    create_directories_for_moving(json_input_string)
