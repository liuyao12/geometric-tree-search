#!/usr/bin/env python3
"""Index the recorded CDCL traversal as a directory tree, grouped by restart.

This indexes actual visits, not an unrolling of the learned proof DAG. Every
recorded event appears exactly once. Decisions are folders; conflicts and
backjump/terminal events are selectable leaves. No search is rerun.
"""
import argparse,gzip,json,pathlib,hashlib
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input',default='data/nonacube-search-replay')
ap.add_argument('--output',default='data/nonacube-search-tree');a=ap.parse_args()
src=pathlib.Path(a.input);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
manifest_bytes=(src/'manifest.json').read_bytes();m=json.loads(manifest_bytes)
phases=[];nodes=[];last=[];stack=[];conflict_nodes=[];ordinal=0;start=0;first_conflict=1
# Node: op, a, b, parent, firstChild, nextSibling, conflictOrdinal, subtreeConflicts.
def append(op,a,b,parent,leaf=0):
    n=len(nodes);nodes.append([op,a,b,parent,-1,-1,leaf,1 if leaf else 0]);last.append(-1)
    if parent>=0:
        if last[parent]<0:nodes[parent][4]=n
        else:nodes[last[parent]][5]=n
        last[parent]=n
    return n
def flush():
    if not nodes:return
    for n in range(len(nodes)-1,0,-1):nodes[nodes[n][3]][7]+=nodes[n][7]
    name=f'phase-{len(phases)+1:04d}.json.gz'
    payload={'start':start,'nodes':nodes,'conflicts':conflict_nodes}
    raw=json.dumps(payload,separators=(',',':')).encode()
    compressed=gzip.compress(raw,mtime=0);(out/name).write_bytes(compressed)
    phases.append({'number':len(phases)+1,'start':start,'end':start+len(nodes)-1,
        'firstConflict':first_conflict,'conflictCount':len(conflict_nodes),
        'nodeCount':len(nodes),'file':name,'sha256':hashlib.sha256(compressed).hexdigest()})
for chunk in m['chunks']:
    c=json.loads(gzip.decompress((src/chunk['file']).read_bytes()))
    for offset,(op,x,y,*_) in enumerate(c['frames']):
        frame=c['start']+offset
        if op==6:
            assert not stack,'Restart with retained decisions is unsupported'
            flush();nodes=[];last=[];conflict_nodes=[];start=frame;first_conflict=ordinal+1
            assert x==len(phases)+1 and y==0
            append(op,x,y,-1)
        else:
            parent=stack[-1] if stack else 0
            if op==3:
                assert len(stack)==y,(frame,len(stack),y)
                stack.append(append(op,x,y,parent))
            elif op==4:
                assert len(stack)==x
                ordinal+=1;conflict_nodes.append(append(op,x,y,parent,ordinal))
            elif op==5:
                assert 0<=x<len(stack)
                append(op,x,y,parent);stack=stack[:x]
            elif op==7:
                assert x==0 and not stack;append(op,x,y,parent)
            else:raise AssertionError(op)
flush()
assert ordinal==m['counts']['conflicts']
index={'version':1,'nodeFields':['op','a','b','parent','firstChild','nextSibling','conflictOrdinal','subtreeConflicts'],
    'semantics':'Directory of actual CDCL visits. Decisions are folders. Conflicts, backjumps and the terminal result are leaves. Restarts group separate search phases; learned pruning is not expanded into unvisited branches.',
    'frames':m['frames'],'conflicts':ordinal,'decisions':m['counts']['decisions'],
    'sourceManifestSHA256':hashlib.sha256(manifest_bytes).hexdigest(),
    'largestFrame':m['largestConnected']['frame'],'phases':phases}
(out/'index.json').write_text(json.dumps(index,separators=(',',':'))+'\n')
print(json.dumps({'phases':len(phases),'nodes':sum(p['nodeCount'] for p in phases),'conflictLeaves':ordinal}))
