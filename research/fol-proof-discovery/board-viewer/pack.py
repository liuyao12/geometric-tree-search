"""Build the static viewer from a verified tiled search tape."""

import argparse
from array import array
import json
from pathlib import Path
import shutil
import sys
from tile_syntax import CATEGORIES


def add_proof(tape, stages, output, source):
    # Keep supporting tapes exported without a corresponding certificate.
    if not (tape.parent/'certificate.json').is_file():
        return
    if not any(stage['goal']=='unbounded-primes' and stage['status']=='proved' for stage in stages):
        return
    sys.path.insert(0,str(source.parent))
    from proof_view import render
    from tiling_view import render as render_tiling

    render(tape.parent,output)
    render_tiling(tape.parent,output)
    for name in ('proof.css','tiling.css','tiling.js'):
        shutil.copyfile(source/name,output/name)
    index=output/'index.html'
    index.write_text(index.read_text().replace('<!-- proof-link -->',
                     '<nav class="view-links proof-link" aria-label="Prime proof views">'
                     '<a href="tiling.html">Explore the proof tiling</a>'
                     '<a href="proof.html">Read the checked proof</a></nav>'))


def build(tape, output, syntax_bin=None):
    stages = json.loads(tape.read_text())
    largest_slot = max(len(a['inputs'])+len(a['rows']) for s in stages for a in s['attempts'])
    bits = 16 if largest_slot <= 65_536 else 32
    rows = array('H' if bits == 16 else 'I')
    chapters = []
    first_mark = 0
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
                                 syntaxFirst=first_mark,
                                 width=board['width'], offers=board['offers'], status=board['status'],
                                 priority=board['preference'], limit=board['limit'], samples=samples))
            first_mark += len(board['inputs']) + len(board['rows'])
        chapters.append(dict(goal=stage['goal'], imports=stage['imports'], status=stage['status'],
                             attempts=attempts))
    output.mkdir(parents=True,exist_ok=True)
    if sys.byteorder!='little':
        rows.byteswap()
    (output/'parents.bin').write_bytes(rows.tobytes())
    palette = []
    if syntax_bin is not None:
        if syntax_bin.stat().st_size != first_mark:
            raise ValueError('Syntax map length does not match the search tape')
        shutil.copyfile(syntax_bin,output/'syntax.bin')
        palette = [dict(label=label,color=color) for _,label,color in CATEGORIES]
    (output/'trace.json').write_text(json.dumps(dict(bits=bits, chapters=chapters, syntax=palette),
                                                separators=(',', ':'))+'\n')
    source=Path(__file__).resolve().parent
    for name in ('index.html','viewer.css','viewer.js'):
        shutil.copyfile(source/name,output/name)
    add_proof(tape,stages,output,source)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tape',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--syntax-bin',type=Path)
    args=parser.parse_args()
    build(args.tape,args.output,args.syntax_bin)
