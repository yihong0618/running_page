#!/bin/bash
source ~/.profile
## Create neccesary files if they don't exist
if [ ! -f "/root/running_page/data/activities.json" ]; then
    touch "/root/running_page/data/activities.json"
    echo "Created new file: /root/running_page/data/activities.json"
fi
if [ ! -f "/root/running_page/data/imported.json" ]; then
    touch "/root/running_page/data/imported.json"
    echo "Created new file: /root/running_page/data/imported.json"
fi
if [ ! -f "/root/running_page/data/data.db" ]; then
    touch "/root/running_page/data/data.db"
    echo "Created new file: /root/running_page/data/data.db"
fi

if [[ "$UNITS" == "imperial" ]]; then
    export VITE_USE_IMPERIAL=true
else
    export UNITS="metric"
fi
if [[ -z "$ATHLETE_NAME" ]]; then
    echo "ATHLETE_NAME is not set, see dotenv"
    export ATHLETE_NAME="My Name"
fi
if [[ -z "$BIRTH_YM" ]]; then
    echo "BIRTH_YM is not set, see dotenv"
    export BIRTH_YM="2001-01"
fi
if [[ -z "$TITLE" ]]; then
    echo "TITLE is not set, see dotenv"
    export TITLE="runner"
fi
if [[ "$ONLY_RUN" == "true" ]]; then
    echo "Garmin with sync only runs"
    export ONLY_RUN="--only-run"
else
    export ONLY_RUN=""
fi
function build_stats {
	echo $APP
	if [ "$APP" = "NRC" ] ; then
		python3 run_page/nike_sync.py ${NIKE_REFRESH_TOKEN}
	elif [ "$APP" = "Garmin" ] ; then
		python3 run_page/garmin_sync.py ${SECRET_STRING} $ONLY_RUN
	elif [ "$APP" = "Garmin-CN" ] ; then
		python3 run_page/garmin_sync.py ${SECRET_STRING} --is-cn $ONLY_RUN
	elif [ "$APP" = "Strava" ] ; then
		python3 run_page/strava_sync.py ${CLIENT_ID} ${CLIENT_SECRET} ${REFRESH_TOKEN}
	elif [ "$APP" = "Nike_to_Strava" ] ; then
		python3 run_page/nike_to_strava_sync.py ${NIKE_REFRESH_TOKEN} ${CLIENT_ID} ${CLIENT_SECRET} ${REFRESH_TOKEN}
	elif [ "$APP" = "Keep" ] ; then
		python3 run_page/keep_sync.py ${KEEP_PHONE_NUMBER} ${KEEP_PASSWORD}
	else
		echo "Unknown app"
		echo "using demo data"
		curl -o data/activities.json https://raw.githubusercontent.com/yihong0618/running_page/refs/heads/master/src/static/activities.json
	fi
	rm dist/assets/*.svg
	python3 run_page/gen_svg.py --type grid --from-db --units $UNITS --athlete "$ATHLETE_NAME" --output assets/grid.svg --use-localtime\
	  --title "$TITLE Grid" \
	  --min-distance 6.0 \
	  --special-color yellow \
	  --special-color2 red \
	  --special-distance 10 \
	  --special-distance2 15
	python3 run_page/gen_svg.py --type circular --from-db --units $UNITS --use-localtime
	python3 run_page/gen_svg.py --type github --from-db --units $UNITS --athlete "$ATHLETE_NAME" --output assets/github.svg --use-localtime \
	  --title "$TITLE GitHub" \
	  --min-distance 0.5 \
	  --special-distance 6 \
	  --special-distance2 13 \
	  --special-color yellow \
	  --special-color2 red
	python3 run_page/gen_svg.py --type monthoflife --from-db --units $UNITS --athlete "$ATHLETE_NAME" --birth $BIRTH_YM --output assets/mol.svg --use-localtime \
	  --special-distance 100 \
	  --special-distance2 200 \
	  --special-color '#f9d367' \
	  --special-color2 '#f0a1a8' \
	  --title "$TITLE Month of Life"
	python3 run_page/gen_svg.py --type year_summary --from-db --units $UNITS --athlete "$ATHLETE_NAME" --birth $BIRTH_YM --output assets/year_summary.svg --use-localtime \
	  --special-distance 13 \
	  --special-color '#f9d367' \
	  --title "$TITLE Year Summary"
	rm dist/assets/*.{js,css}
    pnpm run build
	cp assets/*.svg dist/assets/
}

if [[ "$1" == "24h" ]]; then
	while true; do
	    FILE="dist/index.html"
	    if [[ -z $(find "$FILE" -mmin -1440 2>/dev/null) ]]; then
	      echo "Rebuilding stats at $(date +%F-%H%M)"
	      build_stats
		  echo "Will build again at $(date -d "+24 hours" +%F-%H%M)"
	    else
		MOD_TIME=$(stat -c %Y "$FILE")
		FUTURE_TIME=$((MOD_TIME + 86400))
		READABLE_TIME=$(date -d "@$FUTURE_TIME" "+%Y-%m-%d %H:%M:%S")
	      echo "Waiting... will check at $READABLE_TIME"
	    fi
	    sleep 24h
	done
else
	echo "Rebuilding stats once"
	build_stats
fi