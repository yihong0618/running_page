#!/bin/bash

python3 run_page/gen_svg.py --from-db --type circular --use-localtime
python3 run_page/gen_svg.py --from-db --type monthoflife --birth 1992-06 --special-distance 5 --special-distance2 10 --special-color '#f9d367'  --special-color2 '#f0a1a8' --output assets/mol.svg --use-localtime --athlete gumuxi --title 'Runner Month of Life'