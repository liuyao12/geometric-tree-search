"""Independent XOR lifting of selected covers to binary decorated variants."""
import json
import hashlib
from pathlib import Path
from collections import defaultdict
import sys

m=json.loads(Path(sys.argv[1]).read_text());d=json.loads(Path(sys.argv[2]).read_text());training=sys.argv[4]=='training'
assert m['allContrastFeasible'] and m['objectiveAttained']==m['objectiveUpperBound']==len(m['admittedTypes'])
assert set(m['contrasts'])==set(m['ports'])==set(map(str,m['admittedTypes'])) and all(v==1 for v in m['contrasts'].values())
byid={c['id']:c for c in d['configurations']};checked=0;failed=[]
assert m['dictionaryHash']==(hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest() if training else d['sourceDictionaryHash'])
for ti,bits in m['ports'].items():assert len(bits)==len(d['types'][int(ti)]['positions']) and set(bits)=={0,1}
if training:assert m['selectionHashes']==[hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sys.argv[5:]]
for path in sys.argv[5:]:
    selection=json.loads(Path(path).read_text())
    for r in selection['results']:
        c=byid[r['id']]
        if c['training']!=training:continue
        assert r['status']=='connected positive finite cover' and len(set(r['selected']))==len(r['selected'])
        points=defaultdict(list);adj=defaultdict(list)
        for index in r['selected']:
            o=c['occurrences'][index];assert o['matched'];bits=m['ports'][str(o['type'])];contrast=m['contrasts'][str(o['type'])]
            for u,j in enumerate(o['permutation']):points[o['ids'][j]].append((index,bits[u]*contrast))
        assert len(points)==c['atoms'] and all(len(v)==2 for v in points.values())
        for values in points.values():
            (a,x),(b,y)=values;adj[a].append((b,x^y));adj[b].append((a,x^y))
        color={};consistent=True
        for start in r['selected']:
            if start in color:continue
            color[start]=0;queue=[start]
            for a in queue:
                for b,xor in adj[a]:
                    if b not in color:color[b]=color[a]^xor;queue.append(b)
                    elif color[b]!=(color[a]^xor):consistent=False
        if consistent:
            for values in points.values():assert len({color[a]^x for a,x in values})==1
        else:failed.append(c['id'])
        checked+=1
out={'checkedSelectedCovers':checked,'binaryLiftableCovers':checked-len(failed),'failedConfigurations':failed,
 'training':training,'scope':'Existence of a binary marking lift for supplied selected covers. Selection-induced even-cycle bias; not a learned physical law or preservation of all unmarked tilings.'}
with Path(sys.argv[3]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
