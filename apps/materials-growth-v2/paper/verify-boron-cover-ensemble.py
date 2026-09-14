"""Independent integer cover checks and pooled marking graph reconstruction."""
import hashlib
import json
from pathlib import Path
import sys

def verify(training,selections,ensembles):
    reports=[]
    for fold in range(6):
        raw=(Path(training)/str(fold)/'training-dictionary.json').read_bytes();d=json.loads(raw)
        sr=(Path(selections)/f'{fold}.json').read_bytes();s=json.loads(sr)
        e=json.loads((Path(ensembles)/f'{fold}.json').read_text())
        assert e['trainingDictionaryHash']==hashlib.sha256(raw).hexdigest() and e['selectedArtifactHash']==hashlib.sha256(sr).hexdigest()
        assert e['covers'][0]==s['trainingTrials'][-1]['fits'] and e['k']==s['trainingTrials'][-1]['k']
        n=3*len(d['types']);old=e['snapshots'][0]['labels'];conflicting_covers=0;total_covers=0
        for bundle in e['covers']:
            for c,fit in zip(d['configurations'],bundle):
                assert c['file']==fit['file'];assert len(set(fit['selected']))==len(fit['selected'])
                counts=[0]*c['atoms'];marks=[set() for _ in counts];identities=set()
                for index in fit['selected']:
                    assert 0<=index<len(c['occurrences']);o=c['occurrences'][index]
                    identity=(o['type'],tuple(sorted(o['ids'])));assert identity not in identities;identities.add(identity)
                    for u,p in enumerate(o['permutation']):
                        point=o['ids'][p];counts[point]+=1;label=old[3*o['type']+u]
                        if label is not None:marks[point].add(label)
                assert all(count==e['k'] for count in counts)
                total_covers+=1;conflicting_covers+=any(len(values)>1 for values in marks)
        for snapshot in e['snapshots']:
            adj=[set() for _ in range(n)];observed=set()
            def edge(a,b):adj[a].add(b);adj[b].add(a)
            for bundle in e['covers'][:snapshot['additionalCoversPerConfiguration']+1]:
                for c,fit in zip(d['configurations'],bundle):
                    groups=[[] for _ in range(c['atoms'])]
                    for index in fit['selected']:
                        o=c['occurrences'][index]
                        for u,p in enumerate(o['permutation']):
                            v=3*o['type']+u;observed.add(v);groups[o['ids'][p]].append(v)
                    for g in groups:
                        for v in g[1:]:edge(g[0],v)
            for t in d['types']:
                for a,b in t['symmetryTies']:edge(3*t['id']+a,3*t['id']+b)
            unseen=set(range(n));used_labels=set();assigned=0
            while unseen:
                root=unseen.pop();component={root};todo=[root]
                while todo:
                    for v in adj[todo.pop()]&unseen:unseen.remove(v);component.add(v);todo.append(v)
                labels={snapshot['labels'][v] for v in component};assert len(labels)==1;label=next(iter(labels))
                if component&observed:
                    assert label is not None and label not in used_labels;used_labels.add(label);assigned+=len(component)
                else:assert label is None
            assert len(used_labels)==snapshot['classes'] and assigned==snapshot['assignedVariables']
            assert len(observed)==snapshot['observedVariables']
        uniques=[len({tuple(sorted(bundle[i]['selected'])) for bundle in e['covers']}) for i in range(5)]
        assert uniques==e['uniqueCoversPerConfiguration']
        reports.append({'fold':fold,'verifiedCovers':total_covers,'additionalCoversConflictingWithOriginalMarks':conflicting_covers,
            'classesByRound':[p['classes'] for p in e['snapshots']],'uniqueCoversPerConfiguration':uniques})
    out={'scope':'Training-cover choice sensitivity, not new physical configurations','results':reports}
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':
    out=verify(*sys.argv[1:4])
    if len(sys.argv)>4:
        with Path(sys.argv[4]).open('x') as f:json.dump(out,f,indent=2)
