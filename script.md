python3 scripts/gen_svg.py --from-db --title "Start to Run" --type github --athlete "WonSikin" --special-distance 5 --special-distance2 10 --special-color yellow --special-color2 red --output assets/github.svg --use-localtime --min-distance 0.5

python3 scripts/gen_svg.py --from-db --title "Over 5km Runs" --type grid --athlete "WonSikin"  --output assets/grid.svg --min-distance 5.0 --special-color yellow --special-color2 red --special-distance 10 --special-distance2 20 --use-localtime


python3 scripts/gen_svg.py --from-db --type circular --use-localtime