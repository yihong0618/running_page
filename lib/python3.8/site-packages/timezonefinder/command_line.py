import argparse

from timezonefinder import TimezoneFinder, TimezoneFinderL

tf = TimezoneFinder()
tfL = TimezoneFinderL()
functions = [
    tf.timezone_at,
    tf.certain_timezone_at,
    tf.closest_timezone_at,
    tfL.timezone_at,
    tfL.timezone_at_land,
    tf.timezone_at_land,
]


# TODO write test case
def main():
    parser = argparse.ArgumentParser(description="parse TimezoneFinder parameters")
    parser.add_argument("lng", type=float, help="longitude to be queried")
    parser.add_argument("lat", type=float, help="latitude to be queried")
    parser.add_argument("-v", action="store_true", help="verbosity flag")
    parser.add_argument(
        "-f",
        "--function",
        type=int,
        choices=[0, 1, 2, 3, 4, 5],
        default=0,
        help="function to be called:"
        "0: TimezoneFinder.timezone_at(), "
        "1: TimezoneFinder.certain_timezone_at(), "
        "2: TimezoneFinder.closest_timezone_at(), "
        "3: TimezoneFinderL.timezone_at(), "
        "4: TimezoneFinderL.timezone_at_land(), "
        "5: TimezoneFinder.timezone_at_land(), ",
    )
    parsed_args = parser.parse_args()  # takes input from sys.argv
    tz = functions[parsed_args.function](lng=parsed_args.lng, lat=parsed_args.lat)
    if parsed_args.v:
        print("Looking for TZ at lat=", parsed_args.lat, " lng=", parsed_args.lng)
        print(
            "Function:",
            ["timezone_at()", "certain_timezone_at()"][parsed_args.function],
        )
        print("Timezone=", tz)
    else:
        print(tz)
