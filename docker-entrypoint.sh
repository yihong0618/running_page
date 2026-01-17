#!/bin/bash
set -e

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
elif [[ -z $APP && ! -f "data/.demo" ]]; then
    echo "Running demo initializaion..."
    curl -o src/static/activities.json https://raw.githubusercontent.com/yihong0618/running_page/refs/heads/master/src/static/activities.json
    echo -n | tee data/{imported.json,data.db,.demo}
    rm data/.live
fi
exec "$@"