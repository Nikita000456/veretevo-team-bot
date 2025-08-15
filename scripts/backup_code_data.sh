#!/bin/bash
set -e
BACKUP_DIR="$(dirname "$0")/../backups"
mkdir -p "$BACKUP_DIR"
TS=$(date +%Y-%m-%d_%H-%M)
ARCHIVE="$BACKUP_DIR/veretevo_code_data_backup_$TS.tar.gz"
tar -czf "$ARCHIVE" \
  ../main.py ../requirements.txt ../run_veretevo.sh ../veretevo-bot.service ../README.md ../DEVELOPMENT_STANDARDS.md ../QUICK_REFERENCE.md \
  ../data/ ../config_veretevo/ ../services_veretevo/ ../handlers_veretevo/ ../utils_veretevo/ ../docs/ ../.github/ ../tests/
echo "Backup created: $ARCHIVE" 