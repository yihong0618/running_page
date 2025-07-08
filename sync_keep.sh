#!/bin/bash
 set -a
source .env
set +a
python run_page/keep_sync.py ${keep_mobile} ${keep_password} --sync-types running
