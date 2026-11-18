#!/usr/bin/env bash
set -euo pipefail
# verify.sh <key.json>: run the public gate on a submission (spec D10).
python3 -m voidwell gate --challenge "$(dirname "$0")/challenge.json" --key "$1"
