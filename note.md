
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

pnpm install

rm -rf run_page/data.db src/static/activities.json
python3 run_page/keep_sync.py xxx xxx --sync-types running hiking cycling

pnpm serve
```


- gpc to tcx: https://gotoes.org/strava/Combine_GPX_TCX_FIT_Files.php