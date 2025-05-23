import xml.etree.ElementTree as ET
import math
import json
import sys
import os
from collections import defaultdict
from datetime import datetime

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of Earth in meters
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_activity_date_and_distance(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}

        time_element = root.find('gpx:metadata/gpx:time', ns) or root.find('metadata/time')
        if time_element is None:
            return None, None, f"Skipping {filepath}: <time> tag not found."

        activity_time_str = time_element.text
        activity_datetime = datetime.strptime(activity_time_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        activity_year = activity_datetime.year
        activity_date_str = activity_datetime.strftime("%Y-%m-%d")

        if not (2019 <= activity_year <= 2022):
            return None, None, f"Skipping {filepath}: Year {activity_year} not in range."

        total_distance = 0.0
        track_points = []
        for trkseg in root.findall('.//gpx:trkseg', ns) or root.findall('.//trkseg'):
            for trkpt in trkseg.findall('.//gpx:trkpt', ns) or trkseg.findall('.//trkpt'):
                try:
                    lat = float(trkpt.get('lat'))
                    lon = float(trkpt.get('lon'))
                    track_points.append({'lat': lat, 'lon': lon})
                except (ValueError, TypeError):
                    continue # Skip malformed points

        if len(track_points) < 2:
            return activity_date_str, 0.0, None # Valid date, 0 distance

        for i in range(len(track_points) - 1):
            total_distance += haversine(track_points[i]['lat'], track_points[i]['lon'],
                                        track_points[i+1]['lat'], track_points[i+1]['lon'])
        return activity_date_str, round(total_distance, 2), None
    except ET.ParseError:
        return None, None, f"Skipping {filepath}: XML ParseError."
    except Exception as e:
        return None, None, f"Skipping {filepath}: Unexpected error {e}."


def main():
    # Read null-terminated file paths from stdin
    file_paths_blob = sys.stdin.buffer.read()
    file_paths = [path for path in file_paths_blob.decode('utf-8').split('\x00') if path]

    if not file_paths:
        print("No file paths provided via stdin.", file=sys.stderr)
        return

    processed_runs = []
    for filepath in file_paths:
        if not os.path.exists(filepath): # Double check file exists
            print(f"Warning: File {filepath} from find not found at processing time. Skipping.", file=sys.stderr)
            continue
        date_str, distance, error_msg = get_activity_date_and_distance(filepath)
        if error_msg:
            # print(error_msg, file=sys.stderr) # Optional: print errors for skipped files
            continue
        if date_str is not None: # distance can be 0.0 for valid files with <2 points
            processed_runs.append({'filepath': filepath, 'date': date_str, 'distance': distance})

    runs_by_date = defaultdict(list)
    for run_info in processed_runs:
        runs_by_date[run_info['date']].append(run_info)

    files_to_move_details = []
    for date, runs in runs_by_date.items():
        if len(runs) > 1:
            longest_run = max(runs, key=lambda x: x['distance'])
            for run_info in runs:
                if run_info['filepath'] != longest_run['filepath']:
                    year = run_info['date'][:4]
                    files_to_move_details.append({
                        'filepath': run_info['filepath'],
                        'year': year
                    })
    
    base_target_dir = "/app/dual_date"
    if files_to_move_details:
        try:
            os.makedirs(base_target_dir, exist_ok=True)
        except OSError as e:
            print(f"Fatal: Error creating base directory {base_target_dir}: {e}", file=sys.stderr)
            return

    rename_commands = []
    for item in files_to_move_details:
        source_filepath = item['filepath'] # Already absolute from find
        year = item['year']
        filename = os.path.basename(source_filepath)
        
        destination_dir = os.path.join(base_target_dir, year)
        try:
            os.makedirs(destination_dir, exist_ok=True) # Ensure year directory exists
        except OSError as e:
            print(f"Fatal: Error creating year directory {destination_dir}: {e}. Cannot generate move command for {filename}", file=sys.stderr)
            continue

        destination_filepath = os.path.join(destination_dir, filename)
        rename_commands.append(f"rename_file(filepath='{source_filepath}', new_filepath='{destination_filepath}')")

    if rename_commands:
        for cmd in rename_commands:
            print(cmd)
    else:
        print("No files identified to be moved or no commands generated.", file=sys.stderr)

if __name__ == "__main__":
    main()
