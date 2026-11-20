#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p build/conformance
python3 scripts/conformance/payload.py > build/conformance/payload.json
node scripts/conformance/sort-payload.mjs build/conformance/payload.json
