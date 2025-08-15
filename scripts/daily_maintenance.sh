#!/bin/bash
set -e
LOG=../logs/daily_maintenance_$(date +%Y-%m-%d).log

# Бэкап
bash $(dirname "$0")/backup_code_data.sh >> "$LOG" 2>&1

# Проверка структуры
python3 $(dirname "$0")/check_structure.py >> "$LOG" 2>&1

echo "[DONE] $(date)" >> "$LOG" 