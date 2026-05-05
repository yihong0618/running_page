#!/usr/bin/env bash
set -euo pipefail

# Quick helper to pull Garmin activities and start local preview.
# Usage:
#   ./scripts_garmin_quickstart.sh --email you@example.com --password 'xxx'
#   ./scripts_garmin_quickstart.sh --email you@example.com --password 'xxx' --is-cn --only-run
#   ./scripts_garmin_quickstart.sh --email you@example.com --no-web

EMAIL=""
PASSWORD=""
IS_CN=false
ONLY_RUN=false
NO_WEB=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --email)
      EMAIL="$2"
      shift 2
      ;;
    --password)
      PASSWORD="$2"
      shift 2
      ;;
    --is-cn)
      IS_CN=true
      shift
      ;;
    --only-run)
      ONLY_RUN=true
      shift
      ;;
    --no-web)
      NO_WEB=true
      shift
      ;;
    -h|--help)
      sed -n '1,18p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$EMAIL" ]]; then
  echo "Error: --email is required."
  exit 1
fi

if [[ -z "$PASSWORD" ]]; then
  read -r -s -p "Garmin password: " PASSWORD
  echo
fi

cn_flag=""
if [[ "$IS_CN" == true ]]; then
  cn_flag="--is-cn"
fi

run_flag=""
if [[ "$ONLY_RUN" == true ]]; then
  run_flag="--only-run"
fi

echo "[1/4] Generating Garmin secret string..."
GARMIN_SECRET_STRING=$(python run_page/get_garmin_secret.py "$EMAIL" "$PASSWORD" $cn_flag)

if [[ -z "$GARMIN_SECRET_STRING" ]]; then
  echo "Failed to get Garmin secret string."
  exit 1
fi

echo "[2/4] Syncing Garmin activities..."
python run_page/garmin_sync.py "$GARMIN_SECRET_STRING" $cn_flag $run_flag

echo "[3/4] Generating SVG from local database..."
python run_page/gen_svg.py --from-db

if [[ "$NO_WEB" == true ]]; then
  echo "[4/4] Done. Skipped local preview because --no-web was set."
  exit 0
fi

echo "[4/4] Starting local preview at http://localhost:5173"
pnpm develop
