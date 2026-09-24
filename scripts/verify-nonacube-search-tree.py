#!/usr/bin/env python3
"""Check every directory edge and leaf against the original chronological trace."""
import argparse,gzip,hashlib,json,pathlib
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--replay',default='data/nonacube-search-replay');ap.add_argument('--tree',default='data/nonacube-search-tree');a=ap.parse_args()
replay=pathlib.Path(a.replay);tree=pathlib.Path(a.tree)
raw=(replay/'manifest.json').read_bytes();m=json.loads(raw);index=json.loads((tree/'index.json').read_text())
assert hashlib.sha256(raw).hexdigest()==index['sourceManifestSHA256']
def events():
    for entry in m['chunks']:
        c=json.loads(gzip.decompress((replay/entry['file']).read_bytes()))
        for i,f in enumerate(c['frames']):yield c['start']+i,f
source=iter(events());frame_count=0;conflict_count=0;stack=[];types={}
for phase in index['phases']:
    packed=(tree/phase['file']).read_bytes();assert hashlib.sha256(packed).hexdigest()==phase['sha256']
    data=json.loads(gzip.decompress(packed));nodes=data['nodes'];assert len(nodes)==phase['nodeCount']
    assert data['start']==phase['start']==frame_count
    expected_conflicts=[];subtree=[0]*len(nodes)
    assert not stack
    for local,node in enumerate(nodes):
        frame,f=next(source);op,x,y=f[:3]
        assert frame==phase['start']+local and node[:3]==[op,x,y]
        types[op]=types.get(op,0)+1
        parent=(stack[-1]-phase['start']) if stack else 0
        if op==6:assert local==0 and node[3]==-1
        else:assert node[3]==parent,(frame,node[3],parent)
        if op==3:assert len(stack)==y;stack.append(frame)
        elif op==4:
            assert len(stack)==x
            conflict_count+=1;assert node[6]==conflict_count and node[4]==-1
            expected_conflicts.append(local);subtree[local]=1
        elif op==5:assert 0<=x<len(stack);del stack[x:]
        elif op==7:assert x==0 and not stack
        if op!=4:assert node[6]==0
        if op not in (3,6):assert node[4]==-1
        if local>0:assert 0<=node[3]<local
        frame_count+=1
    assert expected_conflicts==data['conflicts']
    assert len(expected_conflicts)==phase['conflictCount']
    if expected_conflicts:assert nodes[expected_conflicts[0]][6]==phase['firstConflict']
    assert phase['end']==frame_count-1
    # Walk only first-child/next-sibling directory edges. Every recorded node
    # and conflict must be reachable once, in chronological preorder.
    walked=[];pending=[0]
    while pending:
        n=pending.pop();assert n==len(walked);walked.append(n)
        children=[];c=nodes[n][4];last=-1
        while c>=0:
            assert last<c<len(nodes) and nodes[c][3]==n
            children.append(c);last=c;c=nodes[c][5]
        pending.extend(reversed(children))
    assert len(walked)==len(nodes)
    for n in range(len(nodes)-1,-1,-1):
        assert subtree[n]==nodes[n][7]
        if n:subtree[nodes[n][3]]+=subtree[n]
try:next(source);raise AssertionError('Unindexed source events remain')
except StopIteration:pass
assert frame_count==index['frames']==m['frames']
assert conflict_count==index['conflicts']==m['counts']['conflicts']
assert types[3]==index['decisions'] and types[6]==len(index['phases']) and types[7]==1
print(json.dumps({'verified':True,'reachableEvents':frame_count,'reachableConflictLeaves':conflict_count,'phases':len(index['phases']),'everyParentAndEventMatchesRecording':True}))
