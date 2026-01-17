#!/bin/bash
set -e
[ ! -L "data/GPX_OUT" ] && rm -rf GPX_OUT && mkdir "data/GPX_OUT"; ln -rs data/GPX_OUT GPX_OUT
[ ! -L "data/FIT_OUT" ] && rm -rf FIT_OUT && mkdir "data/FIT_OUT"; ln -rs data/FIT_OUT FIT_OUT
[ ! -L "data/TCX_OUT" ] && rm -rf TCX_OUT && mkdir "data/TCX_OUT"; ln -rs data/TCX_OUT TCX_OUT
[ ! -L "data/dist" ] && rm -rf dist && mkdir "data/dist"; ln -rs data/dist dist

if [[ -n $APP && ! -f "data/.live" ]]; then
    echo "Running initialization tasks for $APP..."
    cd ~/running_page
    pwd
    rm data/.demo
    echo -n | tee data/{imported.json,activities.json,data.db,.live}
    rm src/static/activities.json imported.json run_page/data.db
    ln -rs data/activities.json src/static/activities.json
    ln -rs data/imported.json imported.json
    ln -rs data/data.db run_page/data.db
elif [[ -z $APP && ! -f "data/.demo" && ! -f "data/.live" ]]; then
    echo "Running demo initializaion..."
    curl -o src/static/activities.json https://raw.githubusercontent.com/yihong0618/running_page/refs/heads/master/src/static/activities.json
    echo -n | tee data/{imported.json,data.db,.demo}
    rm data/.live
fi
exec "$@"