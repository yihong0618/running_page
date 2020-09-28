import json

from generator import Generator


def make_activities_file(sql_file, gpx_dir, json_file):
    generator = Generator(sql_file)
    # if you want to update data change False to True
    generator.sync_from_gpx(gpx_dir)
    # generator.sync()
    activities_list = generator.load()
    with open(json_file, "w") as f:
        f.write("const activities = ")
        json.dump(activities_list, f, indent=2)
        f.write(";\n")
        f.write("\n")
        f.write("export {activities};\n")
