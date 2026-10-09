"""Proof-carrying elimination of unsupported types in a fixed coarse library.

Previously eliminated types cannot occur in any complete original-library
tiling. A new checked root failure in the remaining inventory extends that
inductive claim. Unknown types are retained. The remaining set is only a
necessary candidate subsystem, never a certificate that a plane tiling exists.
"""
import dataclasses,gc,hashlib,json,time
from collections import Counter
from pathlib import Path
from coarse_continuation import parent_library,search,check_failure,HERE,DOCS

def main():
    start=time.monotonic();stage=json.loads((DOCS/'multiscale-level1-001.json').read_text())
    children,parents,provenance=parent_library(stage);definitions=children+parents;original=tuple(t.identity for t in parents)
    reference_path=HERE/'results/coarse-continuation-checkpoint.json';reference=json.loads(reference_path.read_text())
    if not reference['complete_catalog'] or reference['active_types']!=list(original):raise ValueError('incomplete initial declared inventory')
    eliminated={r['root']:0 for r in reference['results'] if r['status']=='negative'}
    rounds=[{'round':0,'active':original,'results':reference['results'],'eliminated':sorted(eliminated)}]
    sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('coarse_fixed_point.py','coarse_continuation.py')}
    stable=False
    for level in range(1,5):
        active=tuple(n for n in original if n not in eliminated)
        if not active:stable=True;break
        results=[];new=[]
        for name in active:
            r=search(definitions,active,name,nodes=6000,seconds=20);results.append(r)
            print('round',level,name,r['status'],r['nodes'],'nodes',round(r['seconds'],3),'s',flush=True);gc.collect()
            if r['status']=='negative':
                t=time.monotonic();ok,n=check_failure(definitions,active,name,r['certificate'])
                if not ok:raise AssertionError('independent elimination proof rejected')
                r['independent_failure_audit']={'nodes':n,'seconds':time.monotonic()-t};new.append(name)
                print('audit',name,n,'nodes',round(r['independent_failure_audit']['seconds'],3),'s',flush=True);gc.collect()
        rounds.append({'round':level,'active':active,'results':results,'eliminated':new})
        for n in new:eliminated[n]=level
        remaining=[n for n in original if n not in eliminated]
        stable=not new or not remaining
        output={'definitions':[dataclasses.asdict(t) for t in definitions],'parent_provenance':provenance,
                'original_types':original,'rounds':rounds,'eliminated_at':eliminated,'remaining_types':remaining,
                'stable':stable,'sources':sources,'initial_reference_sha256':hashlib.sha256(reference_path.read_bytes()).hexdigest(),
                'seconds':time.monotonic()-start,'scope':'inductive exclusion from complete tilings by the declared fixed parent library; unresolved types retained; no base turtle non-tiling claim'}
        (HERE/'results/coarse-fixed-point-checkpoint.json').write_text(json.dumps(output,separators=(',',':'))+'\n')
        print('round',level,'new',new,'remaining',remaining,flush=True)
        if stable:break
    print('fixed-point gate finished',len(eliminated),'excluded',stable,'stable',round(time.monotonic()-start,3),'s',flush=True)

if __name__=='__main__':main()
