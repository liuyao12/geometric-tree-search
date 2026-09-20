"""Joint finite context/contact cover, without preselected latent target sites.

Diagnostic combinatorial search, not the reference point-filling scheduler.
Select one frozen context per supplied motif occurrence and partition its
ports into admissible contacts. Shared-point representatives come from those
contacts; they are not supplied by a previous successful assembly.
"""
import hashlib,itertools,json,sys
from collections import Counter
from pathlib import Path
import numpy as np
from ase.geometry import find_mic


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def solve(candidates,contacts,domains,live,validate=lambda chosen,cover:True,limit=100000):
    steps=0;stopped=False
    def cover_ports(remaining,chosen,cover,eligible):
        nonlocal steps,stopped
        if steps>=limit:stopped=True;return None
        steps+=1
        if not remaining:return cover if validate(chosen,cover) else None
        first=min(remaining)
        for ei in eligible:
            block=set(contacts[ei]['supports'])
            if first in block and block<=remaining:
                result=cover_ports(remaining-block,chosen,cover+[ei],eligible)
                if result is not None:return result
                if stopped:return None
        return None
    for chosen in itertools.product(*domains):
        if steps>=limit:stopped=True;break
        steps+=1
        required={p for ci in chosen for p in candidates[ci]['supports']}
        eligible=[ei for ei in live if set(contacts[ei]['supports'])<=required]
        cover=cover_ports(required,chosen,[],eligible)
        if cover is not None:return dict(candidates=list(chosen),contacts=cover),dict(status='witness',nodes=steps)
        if stopped:break
    return None,dict(status='unknown-budget' if stopped else 'exhausted-finite-context-contact-pool',nodes=steps)


def main():
    proposalp,coordp,metap,out=map(Path,sys.argv[1:])
    proposal,coords,meta=[json.loads(p.read_text()) for p in [proposalp,coordp,metap]]
    assert proposal['coordinateHash']==sha(coordp) and proposal['metadataHash']==sha(metap)
    cc={c['id']:c for c in coords['configurations']};mm={m['id']:m for m in meta['configurations']};rows=[]
    for row in proposal['rows']:
        cid=row['configuration'];c=cc[cid]
        if row['imageBound']['status']!='image-bound-verified' or row['tripleUnknown']:
            rows.append(dict(configuration=cid,witness=None,search=dict(status='unknown-proposal-domain',nodes=0)));continue
        active=row['consistency']['candidates']
        domains=[[ci for ci in active if row['candidates'][ci]['cluster']==k] for k in range(row['clusters'])]
        def validate(chosen,cover):
            # Reject colliding representatives, rather than hiding them behind
            # contact-specific point IDs. Other representative choices untested.
            points=np.asarray(c['positions']+[row['contacts'][ei]['position'] for ei in cover])
            for i in range(len(points)):
                if i+1==len(points):continue
                delta,_=find_mic(points[i+1:]-points[i],np.asarray(c['cell']),pbc=True)
                if min(np.linalg.norm(delta,axis=1))<=1e-8:return False
            return True
        witness,stats=solve(row['candidates'],row['contacts'],domains,row['consistency']['contacts'],validate)
        rows.append(dict(configuration=cid,witness=witness,search=stats))
    summary=[]
    for phase in sorted({m['phase'] for m in mm.values()}):
        group=[r for r in rows if mm[r['configuration']]['phase']==phase]
        summary.append(dict(phase=phase,frames=len(group),statuses=dict(Counter(r['search']['status'] for r in group))))
    result=dict(scope=__doc__,proposalHash=sha(proposalp),coordinateHash=sha(coordp),metadataHash=sha(metap),codeHash=sha(Path(__file__)),rows=rows,summary=summary,
                limits='Original target-fitted motif partition and poses are given. This is finite contact-cover search, not GCTS reference scheduling. '
                       'Point representatives closer than 1e-8 are rejected as colliding; alternative continuous representatives unsearched. '
                       'No continuous-space exhaustion, general reconstruction or blind-growth claim.')
    with out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(summary))


if __name__=='__main__':main()
