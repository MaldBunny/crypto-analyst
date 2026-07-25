#!/bin/zsh
set -eu

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"

cd "$PROJECT_DIR"
PYTHONPATH=src /usr/bin/python3 -m crypto_analyst.main \
  --html-output public/reports/latest.html \
  --report-url "${REPORT_URL:-}"
