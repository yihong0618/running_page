#!/usr/bin/env python3
"""
Fix location problems in the activities database.

This script fixes common location-related issues:
1. Activities with "China" as location that should have more specific location data
2. Activities with missing location_country that have valid coordinates
3. Activities with incorrect location data that can be reverse geocoded

Fixes issue #773: add a fix script to fix the location problem
"""

import argparse
import sys
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import polyline
from generator.db import Activity, init_db

# Initialize geocoder
geocoder = Nominatim(user_agent="running_page_location_fix")


def reverse_geocode(lat, lon, max_retries=3):
    """
    Reverse geocode coordinates to get location country.

    Args:
        lat: Latitude
        lon: Longitude
        max_retries: Maximum number of retry attempts

    Returns:
        Location string or None if geocoding fails
    """
    for attempt in range(max_retries):
        try:
            location = geocoder.reverse(f"{lat}, {lon}", language="zh-CN", timeout=10)
            if location:
                return str(location)
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            if attempt < max_retries - 1:
                # Exponential backoff: wait 2^attempt seconds
                wait_time = 2**attempt
                print(f"Geocoding failed, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Geocoding failed after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            print(f"Unexpected error during geocoding: {e}")
            return None

    return None


def get_coordinates_from_polyline(summary_polyline):
    """
    Extract coordinates from encoded polyline.

    Args:
        summary_polyline: Encoded polyline string

    Returns:
        Tuple of (lat, lon) for first point, or None if decoding fails
    """
    if not summary_polyline:
        return None

    try:
        # Decode the polyline to get coordinate points
        decoded_points = polyline.decode(summary_polyline)
        if decoded_points:
            # Return the first point (start of the route)
            lat, lon = decoded_points[0]
            return lat, lon
    except Exception as e:
        print(f"Error decoding polyline: {e}")

    return None


def fix_location_for_activity(session, activity, dry_run=False):
    """
    Fix location for a single activity.

    Args:
        session: Database session
        activity: Activity object
        dry_run: If True, only print what would be changed without saving

    Returns:
        True if location was fixed, False otherwise
    """
    # Check if activity needs location fix
    needs_fix = False
    reason = ""
    new_location = None

    # Case 1: Location is "China" (too generic) - try to get more specific
    if activity.location_country == "China":
        needs_fix = True
        reason = "Location is too generic (China)"

    # Case 2: Location is missing but we have coordinates from summary_polyline
    elif not activity.location_country and activity.summary_polyline:
        needs_fix = True
        reason = "Location is missing but coordinates available"

    if not needs_fix:
        return False

    # Try to extract coordinates from summary_polyline and reverse geocode
    coords = get_coordinates_from_polyline(activity.summary_polyline)

    if coords:
        lat, lon = coords
        print(f"  Extracted coordinates: {lat}, {lon}")

        # Reverse geocode to get better location
        new_location = reverse_geocode(lat, lon)

        if new_location:
            # Check if new location is more specific than "China"
            if new_location != "China" and "China" not in new_location:
                if dry_run:
                    print(
                        f"  Would update location from '{activity.location_country}' to '{new_location}'"
                    )
                else:
                    activity.location_country = new_location
                    session.add(activity)
                return True
            else:
                print(f"  New location still generic: {new_location}")
        else:
            print("  Failed to reverse geocode coordinates")
    else:
        print("  Could not extract coordinates from polyline")

    if dry_run and not new_location:
        print(f"Would attempt to fix activity {activity.run_id}: {reason}")
        return True

    return False


def fix_locations(session, dry_run=False, limit=None):
    """
    Fix location problems for activities in the database.

    Args:
        session: Database session
        dry_run: If True, only print what would be changed without saving
        limit: Maximum number of activities to process (None for all)

    Returns:
        Tuple of (fixed_count, total_checked)
    """
    # Find activities that need location fixes
    query = session.query(Activity).filter(
        (Activity.location_country == "China")
        | (
            (Activity.location_country.is_(None))
            & (Activity.summary_polyline.isnot(None))
        )
    )

    if limit:
        query = query.limit(limit)

    activities = query.all()
    total_checked = len(activities)
    fixed_count = 0

    print(f"Found {total_checked} activities that may need location fixes")

    for i, activity in enumerate(activities, 1):
        print(f"Processing activity {i}/{total_checked} (ID: {activity.run_id})...")

        if fix_location_for_activity(session, activity, dry_run):
            fixed_count += 1
            if not dry_run:
                session.commit()

        # Rate limiting: be nice to geocoding service
        if i < total_checked:
            time.sleep(1)

    return fixed_count, total_checked


def main():
    parser = argparse.ArgumentParser(
        description="Fix location problems in activities database"
    )
    parser.add_argument(
        "--db", default="data.db", help="Path to database file (default: data.db)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--limit", type=int, help="Maximum number of activities to process"
    )

    args = parser.parse_args()

    # Initialize database
    session = init_db(args.db)

    print("=" * 60)
    print("Location Fix Script")
    print("=" * 60)

    if args.dry_run:
        print("DRY RUN MODE: No changes will be saved")
        print()

    try:
        fixed_count, total_checked = fix_locations(
            session, dry_run=args.dry_run, limit=args.limit
        )

        print()
        print("=" * 60)
        print("Summary:")
        print(f"  Total activities checked: {total_checked}")
        print(f"  Activities fixed: {fixed_count}")
        print("=" * 60)

        if args.dry_run:
            print("\nRun without --dry-run to apply changes")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
