"""Verify the shipped chord marking for every full-plane tiling in the demo's two domains.

Run with python3 tests/verify_deep_chords.py (Node on PATH, or set NODE).
Pass --economical to verify the search-tuned preset.
The input is the production geometry and actual marking entries. Search starts
unmarked, admits every geometric orientation, and has no node or time cutoff.
"""

import json
import os
import subprocess
import argparse
from a2_neighborhoods import neighborhoods
from math import lcm
from pathlib import Path

DIRECTIONS = ((2, -1), (-1, 2), (-1, -1))


def contains(x, y, loop):
    inside = False
    for (a, b), (c, d) in zip(loop, loop[1:] + loop[:1]):
        det = (c-a)*(y-b) - (d-b)*(x-a)
        if det == 0 and min(a,c) <= x <= max(a,c) and min(b,d) <= y <= max(b,d):
            return True
        if (b > y) != (d > y) and (det > 0) == (d > b):
            inside = not inside
    return inside


def chord_centers(shape, direction):
    # All polygon crossings lie on a rational grid with this denominator.
    # Doubling it also tests a point in each open interval between crossings.
    a,b = direction
    loop = shape['loop']
    d = 2*lcm(*(abs((v-x)*b - (w-y)*a) or 1 for (x,y),(v,w) in zip(loop,loop[1:]+loop[:1])))
    scaled = [(d*x,d*y) for x,y in loop]
    return [(x,y) for x,y,_ in shape['sites'] if all(
        contains(d*x+i*a,d*y+i*b,scaled) for i in range(-d,d+1))]


def verify(set_id, records):
    shapes = {(s['tile'],s['index']):s for s in records}
    layout = {(t,i,c):chord_centers(shape,d) for (t,i),shape in shapes.items()
              for c,d in enumerate(DIRECTIONS)}
    for s, allowed, balls, possible in neighborhoods(records):
        base = {(x,y,c):v for x,y,c,v in shapes[s,0]['marks'] if not c.startswith('chord')}
        sites = {(x,y) for x,y,_ in shapes[s,0]['sites']}
        assert all((x,y) in sites for x,y,c in base)
        for t,i,dx,dy in allowed:
            for x,y,c,v in shapes[t,i]['marks']:
                if not c.startswith('chord'):
                    assert base.get((x+dx,y+dy,c),v) == v

        emitted = 0
        for x,y,c,v in shapes[s,0]['marks']:
            if not c.startswith('chord'):
                continue
            axis = int(c[5:])
            emitters = {(t,i,x-a,y-b) for t,i in shapes for a,b in layout[t,i,axis]}
            if v == 1:
                assert all(ball & emitters for ball in balls), (s,x,y,c,v)
            else:
                assert v == -1 and not any(possible(t) for t in emitters), (s,x,y,c,v)
            emitted += 1
        print(f'{set_id}/{s}: {len(balls)} unmarked neighborhoods, {emitted} chord signs verified.',flush=True)


if __name__ == '__main__':
    if not __debug__:
        raise SystemExit('Run with assertions enabled.')
    test = Path(__file__).with_name('test_deep_chord_marking.mjs')
    parser = argparse.ArgumentParser()
    parser.add_argument('--economical',action='store_true')
    args = parser.parse_args()
    command = [os.environ.get('NODE','node'),test,'--geometry']
    if args.economical:
        command.append('--economical')
    data = json.loads(subprocess.check_output(command))
    for name, records in data.items():
        verify(name,records)
