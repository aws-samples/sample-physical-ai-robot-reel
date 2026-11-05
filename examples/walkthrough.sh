#!/usr/bin/env bash
# Export, verify, seal a finding, tamper with one value, and watch --verify fail. No download, no AWS account.
# Run from the repository root inside a virtual environment where `pip install ".[lerobot]"` has been done.
set -euo pipefail

WORK="${1:-artifacts/walkthrough}"
rm -rf "$WORK"
python examples/make_synthetic_dataset.py "$WORK/dataset"

echo "== 1. Export episode 1"
robot-reel lerobot "$WORK/dataset" --episode 1 --output "$WORK/episode1"

echo "== 2. Verify: manifest, schema, embedded data; then every camera frame and every value against the source"
robot-reel lerobot "$WORK/episode1" --verify
robot-reel lerobot "$WORK/episode1" --verify --check-media --check-source --dataset "$WORK/dataset"

echo "== 3. Seal one observation (frame 8, channel lift) into the export"
robot-reel lerobot "$WORK/episode1" --mark 8 --signal observation.state/lift --note "Lift passes 0.8 here"

echo "== 4. Change one recorded value in a copy; --verify must fail"
cp -R "$WORK/episode1" "$WORK/tampered"
python - "$WORK/tampered/episode.json" <<'PY'
import json, sys
path = sys.argv[1]
trace = json.load(open(path))
trace["series"][0]["values"][3][0] += 1
json.dump(trace, open(path, "w"), indent=1)
PY
if robot-reel lerobot "$WORK/tampered" --verify; then echo "unexpected: tampered copy verified"; exit 1; fi

echo "Open $WORK/episode1/index.html in a browser; the folder works offline."
