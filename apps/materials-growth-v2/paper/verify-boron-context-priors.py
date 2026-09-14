"""Independent incidence-pair reconstruction of context features and rankings."""
from collections import defaultdict,Counter
from fractions import Fraction
from itertools import combinations
import hashlib
import json
from pathlib import Path
import sys


def verify(input_path,learning_path,prior_path,search_path):
    raw=Path(input_path).read_bytes();lr=Path(learning_path).read_bytes();pr=Path(prior_path).read_bytes()
    d=json.loads(raw);learning=json.loads(lr);prior=json.loads(pr)
    assert prior['inputHash']==learning['inputHash']==hashlib.sha256(raw).hexdigest() and prior['learningHash']==hashlib.sha256(lr).hexdigest()
    roles=learning['result']['roleOfSite'];all_hashes=[]
    for c in d['configurations']:
        incidence=defaultdict(list)
        for i,o in enumerate(c['occurrences']):
            assert len(set(o['ids']))==len(o['ids'])
            for u,point in enumerate(o['ids']):incidence[point].append((i,roles[d['types'][o['type']]['offset']+u]))
        shares=defaultdict(list)
        for entries in incidence.values():
            for (a,ra),(b,rb) in combinations(entries,2):
                assert a<b;shares[(a,b)].append((ra,rb))
        adjacent=[[] for _ in c['occurrences']]
        for (a,b),pairs in shares.items():
            adjacent[a].append((c['occurrences'][b]['type'],sorted(pairs)))
            adjacent[b].append((c['occurrences'][a]['type'],sorted((y,x) for x,y in pairs)))
        hashes=[hashlib.sha256(json.dumps([o['type'],sorted(adjacent[i])],separators=(',',':')).encode()).hexdigest() for i,o in enumerate(c['occurrences'])]
        all_hashes.append(hashes)
    assert len(prior['folds'])==len(d['configurations']);checks=[]
    for target,fold in enumerate(prior['folds']):
        assert fold['excluded']==target and fold['trainingConfigurations']==[i for i in range(len(all_hashes)) if i!=target]
        counts=defaultdict(lambda:[0,0]);types=defaultdict(lambda:[0,0])
        for source in fold['trainingConfigurations']:
            chosen=set(learning['result']['selected'][source])
            for i,(h,o) in enumerate(zip(all_hashes[source],d['configurations'][source]['occurrences'])):
                counts[h][0]+=1;counts[h][1]+=i in chosen;types[o['type']][0]+=1;types[o['type']][1]+=i in chosen
        scores=[];matched=0;matched_hashes=set();assert len(fold['rows'])==len(all_hashes[target])
        for h,o,row in zip(all_hashes[target],d['configurations'][target]['occurrences'],fold['rows']):
            observed,selected=counts[h];n,s=counts[h] if observed else types[o['type']]
            expected={'contextHash':h,'contextObserved':observed,'contextSelected':selected,'source':'context' if observed else 'type-fallback','numerator':s+1,'denominator':n+2}
            assert row==expected;scores.append(Fraction(s+1,n+2))
            if observed:matched+=1;matched_hashes.add(h)
        ranks={score:i for i,score in enumerate(sorted(set(scores)))}
        assert fold['occurrenceRanks']==[ranks[s] for s in scores]
        assert fold['matchedContextOccurrences']==matched and fold['uniqueMatchedContexts']==len(matched_hashes)
        assert fold['uniqueTargetContexts']==len(set(all_hashes[target]))
        checks.append({'fold':target,'candidates':len(scores),'contextMatches':matched,'uniqueContexts':len(set(all_hashes[target])),
                       'sharedContexts':len(matched_hashes),'contextFallbacks':len(scores)-matched,
                       'ambiguousSharedContexts':sum(0<counts[h][1]<counts[h][0] for h in matched_hashes)})
        for marked in (False,True):
            run=json.loads((Path(search_path)/f'{target}-{str(marked).lower()}.json').read_text())
            assert run['inputHash']==prior['inputHash'] and run['learningHash']==prior['learningHash']
            assert run['result']['priorHash']==hashlib.sha256(pr).hexdigest() and run['result']['ordering']=='context-prior'
            assert len(run['model']['candidates'])==len(scores)
            for name,digest in run['researchSourceHashes'].items():assert hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()==digest
    return {'scope':__doc__,'priorHash':hashlib.sha256(pr).hexdigest(),'folds':checks,'verifiedSearchBindings':2*len(checks),
            'limitation':'Target witness withheld only for ranking; geometry and t/m fitted jointly. Shared contexts do not establish shared selection semantics or independent samples.'}


if __name__=='__main__':
    out=verify(*sys.argv[1:5])
    with Path(sys.argv[5]).open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))
