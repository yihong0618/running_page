
import json
from config import (

    JSON_FILE,
    SQL_FILE,

)
#根据data.db生成json文件,Json文件影响页面的展示

from generator import Generator
#def test():
if __name__ == "__main__":
    generator = Generator(SQL_FILE)
    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f, indent=0)