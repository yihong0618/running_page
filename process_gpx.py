import xml.etree.ElementTree as ET
import math
import json
from datetime import datetime

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of Earth in meters

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def process_gpx_files(file_paths):
    results = []
    for filepath in file_paths:
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Namespace dictionary to handle GPX namespace
            ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}

            # Extract activity date and time
            time_element = root.find('gpx:metadata/gpx:time', ns)
            if time_element is None:
                # Try without namespace if not found (some files might not use it consistently)
                time_element = root.find('metadata/time')
                if time_element is None:
                    # print(f"Skipping {filepath}: <time> tag not found in metadata.")
                    continue # Skip if time is not found


            activity_time_str = time_element.text
            activity_datetime = datetime.strptime(activity_time_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
            activity_year = activity_datetime.year
            activity_date_str = activity_datetime.strftime("%Y-%m-%d")

            # Filter by year
            if not (2019 <= activity_year <= 2022):
                # print(f"Skipping {filepath}: Year {activity_year} is not within 2019-2022.")
                continue

            total_distance = 0.0
            track_points = []

            for trkseg in root.findall('.//gpx:trkseg', ns) or root.findall('.//trkseg'):
                for trkpt in trkseg.findall('.//gpx:trkpt', ns) or trkseg.findall('.//trkpt'):
                    try:
                        lat = float(trkpt.get('lat'))
                        lon = float(trkpt.get('lon'))
                        track_points.append({'lat': lat, 'lon': lon})
                    except (ValueError, TypeError) as e:
                        # print(f"Skipping point in {filepath} due to invalid lat/lon: {e}")
                        continue # Skip malformed track points
            
            if len(track_points) < 2:
                # print(f"Skipping {filepath}: Not enough track points to calculate distance.")
                results.append({
                    'filepath': filepath,
                    'date': activity_date_str,
                    'distance': 0.0 # Or handle as an error/skip
                })
                continue


            for i in range(len(track_points) - 1):
                pt1 = track_points[i]
                pt2 = track_points[i+1]
                total_distance += haversine(pt1['lat'], pt1['lon'], pt2['lat'], pt2['lon'])
            
            results.append({
                'filepath': filepath,
                'date': activity_date_str,
                'distance': round(total_distance, 2)
            })

        except ET.ParseError:
            # print(f"Skipping {filepath}: XML ParseError.")
            continue # Skip files that cannot be parsed
        except Exception as e:
            # print(f"Skipping {filepath}: An unexpected error occurred: {e}")
            continue # Skip for any other errors

    return results

if __name__ == "__main__":
    # The list of file paths will be passed as a command-line argument
    # For direct execution or testing, you can populate this list.
    # Example: gpx_file_list = ["/app/GPX_OUT/file1.gpx", "/app/GPX_OUT/file2.gpx"]
    
    import sys
    if len(sys.argv) > 1:
        # Arguments are expected to be file paths separated by newlines in a single string
        gpx_file_list = sys.argv[1].strip().split('\n')
        gpx_file_list = [f.strip() for f in gpx_file_list if f.strip()] # Clean up empty strings
    else:
        # print("No file paths provided as command line arguments.")
        gpx_file_list = [] # Default to empty list if no arguments

    # print(f"Processing {len(gpx_file_list)} files.")
    processed_data = process_gpx_files(gpx_file_list)
    print(json.dumps(processed_data, indent=4))
