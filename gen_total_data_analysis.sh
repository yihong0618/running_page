#!/bin/bash
 set -a
source .env
set +a
python3 run_page/gen_svg.py --from-db --type circular --use-localtime
python3 run_page/gen_svg.py --from-db --type monthoflife --birth ${birth} --special-distance ${special_distance} --special-distance2 ${special_distance2} --special-color '#f9d367'  --special-color2 '#f0a1a8' --output assets/mol.svg --use-localtime --athlete ${athlete} --title 'Runner Month of Life'