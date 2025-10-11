# some code from
# https://github.com/timschneeb/KomootGPX.git
# great thanks

import os
import re
import sys
import argparse
import base64
import requests
from datetime import datetime, timedelta
import gpxpy.gpx
from config import GPX_FOLDER


def extract_user_from_tip(json):
    if (
        "_embedded" in json
        and "creator" in json["_embedded"]
        and "display_name" in json["_embedded"]["creator"]
    ):
        return json["_embedded"]["creator"]["display_name"] + ": "
    return ""


class BasicAuthToken(requests.auth.AuthBase):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __call__(self, r):
        authstr = "Basic " + base64.b64encode(
            bytes(self.key + ":" + self.value, "utf-8")
        ).decode("utf-8")
        r.headers["Authorization"] = authstr
        return r


class KomootApi:
    def __init__(self):
        self.user_id = ""
        self.token = ""

    def __build_header(self):
        if self.user_id and self.token:
            return BasicAuthToken(self.user_id, self.token)
        return None

    @staticmethod
    def __send_request(url, auth, critical=True):
        r = requests.get(url, auth=auth)
        if r.status_code != 200:
            print("Error " + str(r.status_code) + ": " + str(r.json()))
            if critical:
                exit(1)
        return r

    def login(self, email, password):
        print("Logging in...")

        r = self.__send_request(
            "https://api.komoot.de/v006/account/email/" + email + "/",
            BasicAuthToken(email, password),
        )

        self.user_id = r.json()["username"]
        self.token = r.json()["password"]

        print("Logged in as '" + r.json()["user"]["displayname"] + "'")

    def fetch_tours(self, silent=False):
        if not silent:
            print("Fetching tours of user '" + self.user_id + "'...")

        results = {}
        has_next_page = True
        current_uri = "https://api.komoot.de/v007/users/" + self.user_id + "/tours/"
        while has_next_page:
            r = self.__send_request(current_uri, self.__build_header())

            has_next_page = (
                "next" in r.json()["_links"] and "href" in r.json()["_links"]["next"]
            )
            if has_next_page:
                current_uri = r.json()["_links"]["next"]["href"]

            tours = r.json()["_embedded"]["tours"]
            for tour in tours:
                if tour["type"] != "tour_recorded":
                    continue
                results[tour["id"]] = tour

        print("Found " + str(len(results)) + " tours")
        return results

    def fetch_tour(self, tour_id):
        print("Fetching tour '" + tour_id + "'...")

        r = self.__send_request(
            "https://api.komoot.de/v007/tours/"
            + tour_id
            + "?_embedded=coordinates,way_types,"
            "surfaces,directions,participants,"
            "timeline&directions=v2&fields"
            "=timeline&format=coordinate_array"
            "&timeline_highlights_fields=tips,"
            "recommenders",
            self.__build_header(),
        )

        return r.json()

    def fetch_highlight_tips(self, highlight_id):
        print("Fetching highlight '" + highlight_id + "'...")

        r = self.__send_request(
            "https://api.komoot.de/v007/highlights/" + highlight_id + "/tips/",
            self.__build_header(),
            critical=False,
        )

        return r.json()


class Point:
    CONST_UNDEFINED = -9999

    def __init__(self, json):
        self.lat = self.lng = self.time = self.alt = self.CONST_UNDEFINED

        if "lat" not in json and "lng" not in json:
            return
        self.lat = json["lat"]
        self.lng = json["lng"]
        if "alt" in json:
            self.alt = json["alt"]
        if "t" in json:
            self.time = json["t"]

    def is_empty(self):
        return self.lat == self.CONST_UNDEFINED and self.lng == self.CONST_UNDEFINED

    def has_only_coords(self):
        return self.alt == self.CONST_UNDEFINED and self.time == self.CONST_UNDEFINED


class POI:
    def __init__(self, name, point, image_url, url, description, type):
        self.name = name
        self.point = point
        self.url = url
        self.image_url = image_url
        self.description = description
        self.type = type


class GpxCompiler:
    def __init__(self, tour, api, no_poi=False, max_desc_length=-1):
        self.api = api
        self.tour = tour
        self.no_poi = no_poi

        self.route = []
        for coord in tour["_embedded"]["coordinates"]["items"]:
            self.route.append(Point(coord))

        if self.no_poi:
            return

        self.pois = []
        if (
            "timeline" in tour["_embedded"]
            and "_embedded" in tour["_embedded"]["timeline"]
        ):
            for item in tour["_embedded"]["timeline"]["_embedded"]["items"]:
                if item["type"] != "poi" and item["type"] != "highlight":
                    continue

                ref = item["_embedded"]["reference"]
                if item["type"] == "poi":
                    name = "Unknown POI"
                    point = Point({})
                    details = ""

                    if "name" in ref:
                        name = ref["name"]
                    if "location" in ref:
                        point = Point(ref["location"])
                    if "details" in ref:
                        details = ", ".join(str(x["formatted"]) for x in ref["details"])

                    self.pois.append(POI(name, point, "", "", details, "POI"))

                elif item["type"] == "highlight":
                    name = "Unknown Highlight"
                    point = Point({})
                    details = ""
                    image_url = ""
                    url = "https://www.komoot.de/highlight/" + str(ref["id"])

                    if "name" in ref:
                        name = ref["name"]
                    if "mid_point" in ref:
                        point = Point(ref["mid_point"])
                    if "front_image" in ref["_embedded"]:
                        if "src" in ref["_embedded"]["front_image"]:
                            image_url = ref["_embedded"]["front_image"]["src"].split(
                                "?", 1
                            )[0]

                    tips = self.api.fetch_highlight_tips(str(ref["id"]))
                    if "_embedded" in tips and "items" in tips["_embedded"]:
                        details += "\n――――――――――\n".join(
                            str(extract_user_from_tip(x) + x["text"])
                            for x in tips["_embedded"]["items"]
                        )
                    if max_desc_length == 0:
                        details = ""
                    elif max_desc_length > 0 and len(details) > max_desc_length:
                        details = details[: max_desc_length - 3] + "..."

                    self.pois.append(
                        POI(name, point, image_url, url, details, "Highlight")
                    )

    def generate(self):
        gpx = gpxpy.gpx.GPX()
        gpx.name = self.tour["name"]
        if self.tour["type"] == "tour_recorded":
            gpx.name = gpx.name + " (Completed)"
        gpx.description = (
            f"Distance: {str(int(self.tour['distance']) / 1000.0)}km, "
            f"Estimated duration: {str(round(self.tour['duration'] / 3600.0, 2))}h, "
            f"Elevation up: {self.tour['elevation_up']}m, "
            f"Elevation down: {self.tour['elevation_down']}m"
        )
        if "difficulty" in self.tour:
            gpx.description = (
                gpx.description + f", Grade: {self.tour['difficulty']['grade']}"
            )

        gpx.author_name = self.tour["_embedded"]["creator"]["display_name"]
        gpx.author_link = "https://www.komoot.de/user/" + str(
            self.tour["_embedded"]["creator"]["username"]
        )
        gpx.author_link_text = "View " + gpx.author_name + "'s Profile on Komoot"
        gpx.link = "https://www.komoot.de/tour/" + str(self.tour["id"])
        gpx.link_text = "View tour on Komoot"
        gpx.creator = self.tour["_embedded"]["creator"]["display_name"]

        track = gpxpy.gpx.GPXTrack()
        track.name = gpx.name
        track.description = gpx.description
        track.link = gpx.link
        track.link_text = gpx.link_text
        track.link_type = gpx.link_type

        gpx.tracks.append(track)

        segment = gpxpy.gpx.GPXTrackSegment()
        track.segments.append(segment)

        augment_timestamp = self.route[0].time == 0
        start_date = datetime.strptime(self.tour["date"], "%Y-%m-%dT%H:%M:%S.%f%z")

        for coord in self.route:
            point = gpxpy.gpx.GPXTrackPoint(coord.lat, coord.lng)
            if coord.alt != coord.CONST_UNDEFINED:
                point.elevation = coord.alt
            if coord.time != coord.CONST_UNDEFINED:
                if augment_timestamp:
                    point.time = start_date + timedelta(seconds=coord.time / 1000)
                else:
                    point.time = datetime.fromtimestamp(coord.time / 1000)
            segment.points.append(point)

        if not self.no_poi:
            for poi in self.pois:
                wp = gpxpy.gpx.GPXWaypoint(poi.point.lat, poi.point.lng)
                if poi.point.alt != poi.point.CONST_UNDEFINED:
                    wp.elevation = poi.point.alt
                if poi.point.time != poi.point.CONST_UNDEFINED:
                    wp.time = datetime.fromtimestamp(poi.point.time / 1000)

                wp.name = poi.name
                wp.description = poi.description
                wp.source = "Komoot"
                wp.link = poi.url
                wp.link_text = "View POI on Komoot"
                wp.type = poi.type
                wp.comment = poi.image_url

                gpx.waypoints.append(wp)

        return gpx.to_xml()


output_dir_contents = set()


def usage():
    print("komoot_sync.py [options]")
    print("\n" + "[Authentication]")
    print("\t{:<34s} {:<10s}".format("mail", "Login using specified email address"))
    print(
        "\t{:<34s} {:<10s}".format(
            "password", "Use provided password and skip interactive prompt"
        )
    )
    print(
        "\t{:<2s}, {:<30s} {:<10s}".format(
            "-n",
            "--anonymous",
            "Skip authentication, no interactive prompt, valid only with -d",
        )
    )
    print("\n" + "[Tours]")
    print(
        "\t{:<2s}, {:<30s} {:<10s}".format(
            "-r",
            "--remove-deleted",
            "Remove GPX files (from --output dir) without corresponding tour in Komoot (deleted and previous versions)",
        )
    )
    print("\n" + "[Filters]")
    print(
        "\t{:<34s} {:<10s}".format(
            "--start-date=YYYY-MM-DD",
            "Filter tours on or after specified date (optional)",
        )
    )
    print(
        "\t{:<34s} {:<10s}".format(
            "--end-date=YYYY-MM-DD",
            "Filter tours on or before specified date (optional)",
        )
    )
    print("\n" + "[Generator]")
    print(
        "\t{:<2s}, {:<30s} {:<10s}".format(
            "-e", "--no-poi", "Do not include highlights as POIs"
        )
    )


def is_tour_in_date_range(tour, start_date, end_date):
    """Check if a tour falls within the specified date range."""
    if "date" not in tour:
        return True  # If tour has no date info, include it

    tour_date_str = tour["date"][:10]  # Extract YYYY-MM-DD
    tour_date = datetime.strptime(tour_date_str, "%Y-%m-%d").date()

    # If only start_date is provided, include all tours on or after start_date
    if start_date and not end_date and tour_date < start_date:
        return False

    # If only end_date is provided, include all tours on or before end_date
    if end_date and not start_date and tour_date > end_date:
        return False

    # If both dates are provided, ensure tour is within range
    if start_date and end_date and (tour_date < start_date or tour_date > end_date):
        return False

    return True


def date_filter(tours, start_date, end_date):
    # Filter tours by date if specified
    if not start_date and not end_date:
        return tours

    filtered_tours = {}
    for tour_id, tour in tours.items():
        if is_tour_in_date_range(tour, start_date, end_date):
            filtered_tours[tour_id] = tour

    date_criteria = ""
    if start_date and end_date:
        date_criteria = f"between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}"
    elif start_date:
        date_criteria = f"on or after {start_date.strftime('%Y-%m-%d')}"
    elif end_date:
        date_criteria = f"on or before {end_date.strftime('%Y-%m-%d')}"

    print(f"Filtered to {len(filtered_tours)} tours {date_criteria}")
    return filtered_tours


def make_gpx(tour_id, api, no_poi, tour_base):
    tour = None
    if tour_base is None:
        tour_base = api.fetch_tour(str(tour_id))
        tour = tour_base

    # Example date: 2022-01-02T12:26:41.795+01:00

    fullname = f"{tour_id}.gpx"
    path = f"{GPX_FOLDER}/{fullname}"

    if fullname in output_dir_contents:
        output_dir_contents.remove(fullname)

    if os.path.exists(path):
        print(f"{fullname} already exists, skipped")
        return

    if tour is None:
        tour = api.fetch_tour(str(tour_id))
    gpx = GpxCompiler(tour, api, no_poi)

    f = open(path, "w", encoding="utf-8")
    f.write(gpx.generate())
    f.close()

    print(f"GPX file written to '{path}'")


def main(args):
    if args.help:
        usage()
        sys.exit(2)

    mail = args.mail
    pwd = args.password
    anonymous = args.anonymous

    if anonymous and (mail is not None or pwd is not None):
        print("Cannot specify login/password in anonymous mode")
        sys.exit(2)

    remove_deleted = args.remove_deleted

    if anonymous:
        print("Cannot get all user's routes in anonymous mode, use -d")
        sys.exit(2)

    no_poi = args.no_poi

    # Parse date ranges
    start_date = None
    end_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD")
            sys.exit(2)

    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD")
            sys.exit(2)

    gpxpat = re.compile(r"\.gpx$")
    for f in os.listdir(GPX_FOLDER):
        if not os.path.isfile(f) or not gpxpat.match(f):
            next
        output_dir_contents.add(f)

    api = KomootApi()

    if not anonymous:
        api.login(mail, pwd)

        tours = api.fetch_tours()

        tours = date_filter(tours, start_date, end_date)

    for x in tours:
        make_gpx(x, api, no_poi, tours[x])

    if remove_deleted:
        for f in output_dir_contents:
            os.unlink(f"{GPX_FOLDER}/{f}")
            print(f"{f} removed from {GPX_FOLDER}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download Komoot tours and highlights as GPX files.",
        # override the auto-created help from argparse to show usage() instead
        add_help=False,
    )
    parser.add_argument("mail", type=str, help="Email address for login")
    parser.add_argument("password", type=str, help="Password for login")
    parser.add_argument(
        "-n",
        "--anonymous",
        action="store_true",
        default=False,
        help="Login anonymously",
    )
    parser.add_argument(
        "--with-gpx",
        dest="with_gpx",
        action="store_true",
        help="get all komoot data to gpx and download",
    )
    parser.add_argument(
        "-r",
        "--remove-deleted",
        action="store_true",
        help="Remove gpx files for nonexistent tours",
    )
    parser.add_argument(
        "-e", "--no-poi", action="store_true", help="Do not include POIs in GPX"
    )
    parser.add_argument(
        "--start-date", type=str, help="Filter tours on or after this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date", type=str, help="Filter tours on or before this date (YYYY-MM-DD)"
    )
    parser.add_argument("-h", "--help", action="store_true", help="Prints help")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        main(args)
    except KeyboardInterrupt as e:
        print(f"Aborted by user: {e}")
        sys.exit(1)
    # except Exception as e:
    #     print(f"Something else went wrong: {e}")
    #     sys.exit(1)
