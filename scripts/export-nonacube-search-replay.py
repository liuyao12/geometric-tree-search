#!/usr/bin/env python3
"""Replay every recorded tile delta; verify stable patches and export seekable chunks.

Largest means maximum among propagation-complete pre-decision states in this
one run, including the fixed root. It is not a global packing maximum.
"""
import argparse, gzip, hashlib, importlib.util, json, pathlib, struct, time
from collections import defaultdict, Counter
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--events',required=True);ap.add_argument('--result',required=True)
ap.add_argument('--output',required=True);a=ap.parse_args()
out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('corona',pathlib.Path(__file__).with_name('search-nonacube-two-corona.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);d=m.build()
universe=d['universe'];root=d['root'];cellsets=[None]+[m.cells(s) for s in universe]
byvoxel=defaultdict(int)
for i,vs in enumerate(cellsets[1:],1):
    for q in vs:byvoxel[q]|=1<<(i-1)
near=m.halo(root)-root
firstbits=0
for q in near:firstbits|=byvoxel[q]
adj={}
def connected(bits):
    reached=0;todo=bits&firstbits
    while todo:
        bit=todo&-todo;todo^=bit;reached|=bit;i=bit.bit_length()
        if i not in adj:
            mask=0
            for q in m.halo(cellsets[i]):mask|=byvoxel[q]
            adj[i]=mask
        todo|=adj[i]&bits&~reached
    return reached
def ids(bits):
    result=[]
    while bits:
        b=bits&-bits;bits^=b;result.append(b.bit_length())
    return result
def certificate(chosen,frame):
    occupied=set(root);touching=[]
    for i in chosen:
        assert not occupied&cellsets[i]
        occupied.update(cellsets[i])
        if cellsets[i]&near:touching.append(i)
    inner=root.union(*(cellsets[i] for i in touching))
    second=m.halo(inner)-inner
    return dict(frame=frame,tileCount=len(chosen)+1,selected=chosen,root=sorted(root),
        tiles=[sorted(cellsets[i]) for i in chosen],firstLayerTiles=len(touching),
        rootHaloCovered=len(near&occupied),rootHaloRequired=len(near),
        secondHaloCovered=len(second&occupied),secondHaloRequired=len(second))
occupied=Counter(root);overlap=0;live=set();bits=0;delta=[]
frames=[];chunks=[];frame_count=0;chunk_initial=[];counts=Counter();stable=0
best_count=0;best_connected_count=0;best=None;best_connected=None
chunk_counters={'decisions':0,'conflicts':0,'backtracks':0,'searchStarts':0}
def counters():return dict(decisions=counts[3],conflicts=counts[4],backtracks=counts[5],searchStarts=counts[6])
def flush():
    global frames,chunk_initial,chunk_counters
    if not frames:return
    name=f'chunk-{len(chunks):04d}.json.gz'
    payload=dict(start=frame_count-len(frames),initial=chunk_initial,counters=chunk_counters,frames=frames)
    raw=json.dumps(payload,separators=(',',':')).encode()
    (out/name).write_bytes(gzip.compress(raw,mtime=0))
    chunks.append(dict(file=name,start=payload['start'],count=len(frames),bytes=(out/name).stat().st_size))
    frames=[];chunk_initial=sorted(live);chunk_counters=counters()
begun=time.monotonic()
with open(a.events,'rb') as f:
    while block:=f.read(12*65536):
        assert len(block)%12==0
        for op,x,y in struct.iter_unpack('<iii',block):
            if op in (1,2):
                assert 1<=x<=len(universe)
                if op==1:
                    assert x not in live
                    live.add(x);bits|=1<<(x-1);delta.append(x)
                    for q in cellsets[x]:
                        occupied[q]+=1
                        if occupied[q]==2:overlap+=1
                else:
                    assert x in live
                    live.remove(x);bits^=1<<(x-1);delta.append(-x)
                    for q in cellsets[x]:
                        if occupied[q]==2:overlap-=1
                        occupied[q]-=1
                continue
            # Preserve enqueue/undo ordering, including solver simplifications.
            assert op in (3,4,5,6,7)
            counts[op]+=1
            if op==3:
                assert overlap==0, 'Propagation-complete decision has overlapping tiles'
                stable+=1
                if len(live)+1>best_count:
                    best_count=len(live)+1;best=certificate(sorted(live),frame_count)
                if len(live)+1>best_connected_count:
                    component=connected(bits);n=bin(component).count('1')+1
                    if n>best_connected_count:
                        best_connected_count=n;best_connected=certificate(ids(component),frame_count)
            frames.append([op,x,y,delta,len(live)+1,overlap]);delta=[]
            frame_count+=1
            if len(frames)==4096:flush()
flush()
assert counts[7]==1 and op==7 and x==0
result=json.loads(pathlib.Path(a.result).read_text())
assert counts[3]==result['decisions'] and counts[4]==result['conflicts'] and counts[6]==result['searchStarts']
manifest=dict(version=1,scope='Integer translations, all three cubic orientations, full face/edge/vertex coronas.',
    semantics='Complete chronological CDCL run; every decision, conflict, backjump and restart. Positive tile assignments only; auxiliary propagation omitted.',
    largestDefinition='Maximum at propagation-complete pre-decision states in this run, including the root; not a global packing maximum.',
    solver=result,frames=frame_count,chunks=chunks,counts=counters(),verifiedStableStates=stable,
    placements=universe,root=sorted(root),largest=best,largestConnected=best_connected,
    eventsSHA256=hashlib.sha256(pathlib.Path(a.events).read_bytes()).hexdigest(),
    formulaSHA256='d5b60a0a7257daebd8bc07b264b00b0af51a1313963874f1e084f13843a65185')
(out/'manifest.json').write_text(json.dumps(manifest,separators=(',',':'))+'\n')
(out/'largest-connected.json').write_text(json.dumps(best_connected,indent=2)+'\n')
print(json.dumps(dict(frames=frame_count,chunks=len(chunks),counts=counters(),largest=best_count,
    largestConnected=best_connected_count,largestConnectedFrame=best_connected['frame'],seconds=time.monotonic()-begun)),flush=True)
