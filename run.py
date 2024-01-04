#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time     : 2024/1/4 18:11
# @Filename : run.py
# @Author   : Alan_Hsu
import subprocess
import os

import platform
import time


def run_test():
  system_name = platform.system()  # 获取系统名称
  if system_name.lower() == 'windows':
    run_command = "python run_page/keep_sync.py 18310687663 Boeai880521 --with-gpx"
    time.sleep(5)


  else:
    # 生成keep 数据
    run_command = "python run_page/keep_sync.py 18310687663 Boeai880521 --with-gpx"
    time.sleep(5)
    # 生成 5km 路线图
    run_command = "python3 run_page/gen_svg.py --from-db --title 'Alan_Hsu Running' --type github --athlete 'Alan_Hsu' --special-distance 5 --special-distance2 10 --special-color yellow --special-color2 red --output assets/github.svg --use-localtime --min-distance 0.5"
    time.sleep(3)
    run_command = "python3 run_page/gen_svg.py --from-db --title 'Over 5km Runs' --type grid --athlete 'Alan_Hsu'  --output assets/grid.svg --min-distance 5.0 --special-color yellow --special-color2 red --special-distance 10 --special-distance2 40 --use-localtime"
    time.sleep(3)
    # 生成年度环数据
    run_command = "python3 run_page/gen_svg.py --from-db --type circular --use-localtime"
    time.sleep(3)

    # git
    run_command = "git add . && git commit -m 'keep_data update' && git push origin master"

  run_process = subprocess.Popen(run_command, shell=True)
  run_process.wait()


if __name__ == '__main__':

  run_test()
