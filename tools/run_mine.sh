#!/usr/bin/env bash
# Run the GitHub mining pass. The PAT must arrive via the environment.
set -u
cd "$(dirname "$0")/.."
: "${GH_TOKEN:?GH_TOKEN must be set in the environment; never hardcode it here}"
mkdir -p raw manifest
python tools/mine_github.py >raw/mine.log 2>raw/mine.err.log
echo "exit=$? at $(date -Iseconds)" >raw/mine.done