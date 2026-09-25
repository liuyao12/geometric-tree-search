#!/usr/bin/env python3
"""Export a finite conditional point/candidate problem; no solver is invoked."""
import argparse
import json
from pathlib import Path

import encode


def export(shape, prefix):
    shapes = (((0, 0, 0),),) if shape == 'cube' else encode.SHAPES
    data = encode.geometry(shapes)
    prefix = Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    stats = encode.write(data, prefix.with_suffix('.cnf'), prefix.with_suffix('.placements.txt'))
    ids, near = data['ids'], data['near']
    triggers = {}
    for s in sorted(data['first']):
        for q in data['requirements'][s]:
            triggers.setdefault(q, []).append(ids[s])
    points = sorted(data['target'])
    covers = data['by_voxel']
    # Every finite target obligation has fixed generation zero, even while
    # dormant. This is a finite conditional-target adaptation, not growth.
    lines = [f'{len(ids)} {len(points)}']
    for q in points:
        c, t = covers[q], sorted(triggers.get(q, []))
        lines.append(' '.join(map(str, [*q, 0, int(q in near), len(c), len(t), *c, *t])))
    Path(prefix).with_suffix('.points').write_text('\n'.join(lines) + '\n')
    return {**stats, 'points': len(points), 'shape': shape}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--shape', choices=['nonacube', 'cube'], default='nonacube')
    p.add_argument('--prefix', required=True)
    a = p.parse_args()
    print(json.dumps(export(a.shape, a.prefix)))
