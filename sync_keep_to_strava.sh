#!/bin/bash
 set -a
source .env
set +a
python run_page/keep_to_strava_sync.py ${keep_mobile} ${keep_password} ${client_id} ${client_secret} ${strava_refresh_token} --sync-types  running cycling hiking
