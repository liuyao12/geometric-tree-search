"""Read production geometry on stdin. Output all surviving unmarked second neighborhoods."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tests'))
from a2_neighborhoods import neighborhoods

if not __debug__:
    raise SystemExit('Run with assertions enabled.')
out = {}
for set_id, geometry in json.load(sys.stdin).items():
    centers = {}
    for tile, allowed, balls, _ in neighborhoods(geometry):
        centers[tile] = {'neighbors':sorted(allowed), 'balls':sorted(sorted(b) for b in balls)}
    out[set_id] = {'geometry':geometry, 'centers':centers}
json.dump(out, sys.stdout, separators=(',', ':'))
