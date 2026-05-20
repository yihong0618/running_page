#!/bin/bash
set -e
[ ! -d "data/GPX_OUT" ] && mkdir data/GPX_OUT 
[ ! -d "data/FIT_OUT" ] && mkdir data/FIT_OUT 
[ ! -d "data/TCX_OUT" ] && mkdir data/TCX_OUT 
[ ! -d "data/dist" ] && mkdir data/dist
[ ! -L "GPX_OUT" ] && rm -rf GPX_OUT && ln -s data/GPX_OUT GPX_OUT
[ ! -L "FIT_OUT" ] && rm -rf FIT_OUT && ln -s data/FIT_OUT FIT_OUT
[ ! -L "TCX_OUT" ] && rm -rf TCX_OUT && ln -s data/TCX_OUT TCX_OUT
[ ! -L "dist" ]&& rm -rf dist && ln -s data/dist dist

if [[ -n $APP && ! -f "data/.live" ]]; then
    echo "Running with $APP data..."
    echo -n | tee data/{imported.json,activities.json,data.db,.live}
    rm src/static/activities.json imported.json run_page/data.db
    ln -rs data/activities.json src/static/activities.json
    ln -rs data/imported.json imported.json
    ln -rs data/data.db run_page/data.db
    rm data/.demo
elif [[ -z $APP && ! -f "data/.demo" && ! -f "data/.live" ]]; then
    echo "Running with demonstration data..."
    cp ./activities.json data/activities.json
    echo -n | tee data/{imported.json,data.db,.demo}
    rm data/.live
fi
exec "$@"