"""Build the static viewer from a verified tiled search tape."""

import argparse
from array import array
import json
from pathlib import Path
import shutil
import sys


def build(tape, output):
    stages = json.loads(tape.read_text())
    largest_slot = max(len(a['inputs'])+len(a['rows']) for s in stages for a in s['attempts'])
    bits = 16 if largest_slot <= 65_536 else 32
    rows = array('H' if bits == 16 else 'I')
    chapters = []
    for stage in stages:
        attempts = []
        for board in stage['attempts']:
            first = len(rows)//2
            for left, _, right, _, _ in board['rows']:
                rows.extend((left,right))
            samples = [dict(offers=s['offer'], rows=s['frontier']-len(board['inputs']),
                            outcome=s['outcome'], parents=[s['move'][0],s['move'][2]])
                       for s in board['samples']]
            attempts.append(dict(first=first, rows=len(board['rows']), inputs=len(board['inputs']),
                                 width=board['width'], offers=board['offers'], status=board['status'],
                                 priority=board['preference'], limit=board['limit'], samples=samples))
        chapters.append(dict(goal=stage['goal'], imports=stage['imports'], status=stage['status'],
                             attempts=attempts))
    output.mkdir(parents=True,exist_ok=True)
    if sys.byteorder!='little':
        rows.byteswap()
    (output/'parents.bin').write_bytes(rows.tobytes())
    (output/'trace.json').write_text(json.dumps(dict(bits=bits, chapters=chapters),
                                                separators=(',', ':'))+'\n')
    source=Path(__file__).resolve().parent
    for name in ('index.html','viewer.css','viewer.js'):
        shutil.copyfile(source/name,output/name)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tape',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    build(args.tape,args.output)
