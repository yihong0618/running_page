import json
import sys
import os

def generate_move_commands(json_data_string):
    try:
        files_to_move = json.loads(json_data_string)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}", file=sys.stderr)
        return []

    if not isinstance(files_to_move, list):
        print("Error: JSON input is not a list.", file=sys.stderr)
        return []

    commands = []
    for item in files_to_move:
        if not isinstance(item, dict) or 'filepath' not in item or 'year' not in item:
            print(f"Warning: Skipping invalid item in JSON: {item}", file=sys.stderr)
            continue

        source_filepath = item['filepath']
        year = str(item['year']) # Ensure year is a string
        
        # It's good practice to ensure the source file path from JSON is absolute,
        # or resolve it based on a known root if it's relative.
        # Assuming /app/ is the root for filepaths from JSON.
        if not os.path.isabs(source_filepath):
            source_filepath = os.path.join("/app", source_filepath.lstrip('/'))
            
        filename = os.path.basename(source_filepath)
        destination_dir = os.path.join("/app/dual_date", year)
        destination_filepath = os.path.join(destination_dir, filename)
        
        # Construct the tool call string
        # Ensure paths are quoted if they might contain spaces, though not expected here.
        command = f"rename_file(filepath='{source_filepath}', new_filepath='{destination_filepath}')"
        commands.append(command)
            
    return commands

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_input_string = sys.argv[1]
    else:
        json_input_string = sys.stdin.read()

    if not json_input_string.strip():
        print("No JSON input provided.", file=sys.stderr)
        sys.exit(1) # Exit if no input
    
    move_commands = generate_move_commands(json_input_string)
    if move_commands:
        # Print each command on a new line, so they can be reviewed or executed.
        # For direct execution in the agent, the agent would parse this output
        # and call the tool for each command.
        for cmd in move_commands:
            print(cmd)
    else:
        print("No move commands generated.", file=sys.stderr)
