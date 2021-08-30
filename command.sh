python3(python) scripts/keep_sync.py ${your mobile} ${your password}


python3 scripts/gen_svg.py --from-db --title "年度数据Github" --type github --athlete "Eished" --special-distance 10 --special-distance2 20 --special-color yellow --special-color2 red --output assets/github.svg --use-localtime --min-distance 0.5

python3 scripts/gen_svg.py --from-db --title "年度数据网格" --type grid --athlete "Eished"  --output assets/grid.svg --min-distance 5.0 --special-color yellow --special-color2 red --special-distance 20 --special-distance2 40 --use-localtime

python3 scripts/gen_svg.py --from-db --type circular --use-localtime
