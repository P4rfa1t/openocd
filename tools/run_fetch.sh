#!/usr/bin/env bash
# Materialise both tiers of the consolidated inventory.
# Safe to re-run: identical files are left alone, PROVENANCE.json is rebuilt.
#
# NOTE the explicit `-u` on python. Without it, stdout is block-buffered when
# redirected to a file, so a redirected run writes an EMPTY log on completion
# and the diagnostic tail below shows nothing. That masked a crash once.
set -u
cd "$(dirname "$0")/.."
: "${GH_TOKEN:?GH_TOKEN must be set in the environment}"
# Some repos carry filenames that are not valid in the host code page (GBK).
# Force UTF-8 so such paths survive printing and writing.
export PYTHONIOENCODING=utf-8
mkdir -p raw manifest

echo "=== tier 1: tcl/ ==="
python -u tools/fetch_third_party.py --tier 1 >raw/fetch1.log 2>&1
echo "tier1 exit=$?"
tail -14 raw/fetch1.log

echo "=== tier 2: patch worklist ==="
python -u tools/fetch_third_party.py --tier 2 >raw/fetch2.log 2>&1
echo "tier2 exit=$?"
tail -14 raw/fetch2.log

echo "=== verify ==="
python -u tools/verify_tree.py >raw/verify.log 2>&1
echo "verify exit=$?"
tail -24 raw/verify.log

echo "finished at $(date -Iseconds)" >raw/fetch.done
