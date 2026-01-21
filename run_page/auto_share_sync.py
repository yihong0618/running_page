import argparse
from openai import OpenAI
from config import SQL_FILE, PNG_FOLDER
from generator import Generator
import polyline
import base64
import os
import cairosvg  # 替换 svglib.svglib 和 reportlab.graphics

SVG_WIDTH = 800
SVG_HEIGHT = 600
SVG_MARGIN = 30
BACKGROUND_COLOR = "#f8f9fa"
POLYLINE_COLOR = "rgb(224,237,94)"
POLYLINE_WIDTH = 3
START_MARKER_COLOR = "#00FF00"  # Green
END_MARKER_COLOR = "#FF0000"  # Red
DEFAULT_OUTPUT_FILENAME = "route"
PLUS_PROMPT = """roadmap as shown you can do some color optimization.
Write, distance: {distance} km pace: {pace} time: {time} date: {date} and typeset it yourself!
"""

client = None


def generate_share_image(distance, pace, time, date, client):
    """
    Generates a share image with the given parameters.

    Args:
        distance: Distance of the run.
        pace: Pace of the run.
        time: Time taken for the run.
        date: Date of the run.
    """
    base_prompt = "Create a running share image with a running path, add some other contents like running"
    try:
        chat_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative assistant for generating image prompts.",
                },
                {
                    "role": "user",
                    "content": f"Enhance this prompt for a beautiful running share image: {base_prompt}",
                },
            ],
            max_tokens=100,
            temperature=0.8,
        )
        enhanced_prompt = chat_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error enhancing prompt: {e}")
        enhanced_prompt = base_prompt
    prompt = enhanced_prompt + PLUS_PROMPT.format(
        distance=distance,
        pace=pace,
        time=time,
        date=date,
    )

    try:
        result = client.images.edit(
            model="gpt-image-1",
            prompt=prompt,
            image=[open("route.png", "rb")],
            n=1,
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        output_filename = f"share_image_{date}.png"
        output_path = os.path.join(PNG_FOLDER, output_filename)

        os.makedirs(PNG_FOLDER, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        print(f"Share image saved to {output_path}")
    except Exception as e:
        print(f"Error generating share image: {e}")


def generate_route_svg(
    polyline_str, output_filename=DEFAULT_OUTPUT_FILENAME, format="png"
):
    """
    Generates a route visualization from a polyline string.

    Args:
        polyline_str: The encoded polyline string.
        output_filename: The base filename for the output file (without extension).
        format: Output format, either 'svg' or 'png'.
    """
    try:
        points = polyline.decode(polyline_str)
    except Exception as e:
        print(f"Error decoding polyline: {e}")
        return

    if not points:
        print("No coordinate points decoded from polyline.")
        return

    lats = [lat for lat, lon in points]
    lons = [lon for lat, lon in points]

    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    draw_width = SVG_WIDTH - 2 * SVG_MARGIN
    draw_height = SVG_HEIGHT - 2 * SVG_MARGIN

    lon_range = max_lon - min_lon
    lat_range = max_lat - min_lat

    def scale_x(lon):
        if lon_range == 0:
            return SVG_WIDTH / 2
        return SVG_MARGIN + (lon - min_lon) / lon_range * draw_width

    def scale_y(lat):
        if lat_range == 0:
            return SVG_HEIGHT / 2
        return SVG_HEIGHT - SVG_MARGIN - (lat - min_lat) / lat_range * draw_height

    svg_points_str = " ".join(
        f"{scale_x(lon):.2f},{scale_y(lat):.2f}" for lat, lon in points
    )

    start_lat, start_lon = points[0]
    end_lat, end_lon = points[-1]

    svg_content = f"""\
<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">
  <rect width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="{BACKGROUND_COLOR}"/>
  <polyline points="{svg_points_str}" fill="none" stroke="{POLYLINE_COLOR}" stroke-width="{POLYLINE_WIDTH}" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="{scale_x(start_lon):.2f}" cy="{scale_y(start_lat):.2f}" r="5" fill="{START_MARKER_COLOR}" />
  <circle cx="{scale_x(end_lon):.2f}" cy="{scale_y(end_lat):.2f}" r="5" fill="{END_MARKER_COLOR}" />
</svg>"""

    svg_filename = f"{output_filename}.svg"
    png_filename = f"{output_filename}.png"

    try:
        with open(svg_filename, "w", encoding="utf-8") as f:
            f.write(svg_content)

        if format.lower() == "png":
            try:
                cairosvg.svg2png(url=svg_filename, write_to=png_filename)
                os.remove(svg_filename)
                print(f"Route map generated: {png_filename}")
            except Exception as e:
                print(f"Error during PNG conversion: {e}")
        else:
            print(f"Route map generated: {svg_filename}")
    except IOError as e:
        print(f"Error writing file: {e}")
    except Exception as e:
        print(f"Error during conversion: {e}")


def run_auto_sync(client, format="svg", date=None):
    """
    if date is None, get the latest activity
    """
    generator = Generator(SQL_FILE)
    activities_list = generator.load()
    if date:
        activity = next(
            (
                activity
                for activity in activities_list
                if activity["start_date_local"].startswith(date)
            ),
            None,
        )
        if not activity:
            print(f"No activity found for date: {date}")
            return
    else:
        activity = activities_list[-1]

    if "summary_polyline" in activity and activity["summary_polyline"]:
        generate_route_svg(activity["summary_polyline"], format=format)

        distance = round(activity.get("distance", 0) / 1000, 2)
        moving_time = activity.get("moving_time", "")
        date = activity.get("start_date_local", "").split()[0]

        if "average_speed" in activity and activity["average_speed"] > 0:
            pace_seconds = 1000 / activity["average_speed"]
            pace_minutes = int(pace_seconds // 60)
            pace_seconds = int(pace_seconds % 60)
            pace = f"{pace_minutes}:{pace_seconds:02d}"
        else:
            pace = "0:00"

        generate_share_image(distance, pace, moving_time, date, client=client)
    else:
        print("No route data found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate route visualization")
    parser.add_argument(
        "--format",
        choices=["svg", "png"],
        default="png",
        help="Output format: svg or png (default: png)",
    )
    # Initialize OpenAI client
    parser.add_argument("--api_key", required=True, help="OpenAI API key") or os.getenv(
        "OPENAI_API_KEY"
    )
    parser.add_argument("--base_url", default="", help="OpenAI base URL") or os.getenv(
        "OPENAI_BASE_URL"
    )
    parser.add_argument("--date", help="Date of the activity in YYYY-MM-DD format")
    args = parser.parse_args()
    if args.base_url:
        client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    else:
        client = OpenAI(api_key=args.api_key)

    run_auto_sync(format=args.format, client=client, date=args.date)
