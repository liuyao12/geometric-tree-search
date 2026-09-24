#!/usr/bin/env python3
"""Mine a minimal triple and synthesize a CONSTRAINT-valued marking prototype.

Separate SAT control: complete finite core-surround labels, no outer viability
requirement. This is not the existing fixed-value GCTS marking learner.
"""
import argparse,importlib.util,itertools,json,pathlib,time
from collections import defaultdict
from threading import Timer
from pysat.card import CardEnc,EncType
from pysat.solvers import Glucose3
spec=importlib.util.spec_from_file_location('corona',pathlib.Path(__file__).with_name('search-nonacube-two-corona.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def surround(fixed,seconds):
    core=frozenset().union(*(m.cells(s) for s in fixed));target=m.halo(core)-core
    universe=sorted(m.candidates(target,core));by=defaultdict(list)
    for i,s in enumerate(universe,1):
        for q in m.cells(s):by[q].append(i)
    for q in sorted(target):
        if not by[q]:return {'status':'UNSAT','deadPoint':q}
    clauses=[];top=len(universe)
    for q in sorted(by):
        if len(by[q])>1:
            enc=CardEnc.atmost(by[q],1,top_id=top,encoding=EncType.seqcounter);clauses+=enc.clauses;top=enc.nv
    for q in sorted(target):clauses.append(by[q])
    with Glucose3(bootstrap_with=clauses) as solver:
        timer=Timer(seconds,solver.interrupt);timer.daemon=True;timer.start()
        try:answer=solver.solve_limited(expect_interrupt=True)
        finally:timer.cancel();timer.join()
        if answer is not True:return {'status':'UNSAT' if answer is False else 'unknown'}
        positive={v for v in solver.get_model() if v>0}
        chosen=[s for i,s in enumerate(universe,1) if i in positive]
    occupied=set(core)
    for s in chosen:
        assert not m.cells(s)&occupied;occupied.update(m.cells(s))
    assert m.halo(core)<=occupied
    return {'status':'SAT','fixed':fixed,'outer':chosen,'haloCells':len(target)}

def candidates():
    root=(0,(0,0,0));rv=m.cells(root);near=m.halo(rv)-rv
    neighbors=sorted(m.candidates(near,rv));voxels=[m.cells(s) for s in neighbors]
    # A connected triple has a tile adjacent to both others, so this rooted
    # star enumeration covers all connected triples up to choosing the root
    # and a cubic rotation. We stop at the first certified minimal example.
    for p in sorted(near,key=lambda q:(sum(abs(x) for x in q),q)):
        covers=sorted(m.candidates({p},rv));cv=[m.cells(s) for s in covers];full=(1<<len(covers))-1
        masks=[]
        for i,v in enumerate(voxels):
            if p in v:continue
            mask=sum(1<<j for j,w in enumerate(cv) if v&w)
            if mask and mask!=full:masks.append((i,mask))
        for at,(i,a) in enumerate(masks):
            for j,b in masks[at+1:]:
                if a|b==full and not voxels[i]&voxels[j]:yield [root,neighbors[i],neighbors[j]],p

def synthesize(k):
    trials=[]
    for rank in range(1,k+1):
        var=lambda i,v:1+i*rank+v
        clauses=[[-var(i,v) for i in range(k)] for v in range(rank)]
        top=k*rank
        # Every proper subset has a common admissible fiber state; the full
        # patch has none. These are set intersections, not equality markings.
        for mask in range((1<<k)-1):
            witnesses=[]
            for v in range(rank):
                top+=1;witnesses.append(top)
                for i in range(k):
                    if mask&(1<<i):clauses.append([-top,var(i,v)])
            clauses.append(witnesses)
        with Glucose3(bootstrap_with=clauses) as solver:
            sat=solver.solve();trials.append({'fiberStates':rank,'status':'SAT' if sat else 'UNSAT'})
            if sat:
                model=set(solver.get_model());allowed=[sum(1<<v for v in range(rank) if var(i,v) in model) for i in range(k)]
                return {'kind':'constraint-valued-section','fiberStates':rank,'allowedMasks':allowed,'trials':trials,
                    'semantics':'At each marked point/channel, intersect admissible fiber states. Empty intersection rejects. This replaces fixed-value equality only in this isolated prototype.'}
    raise AssertionError('Generic k-role construction should exist')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',default='data/nonacube-patch-constraints/study.json');ap.add_argument('--attempts',type=int,default=100);ap.add_argument('--seconds',type=float,default=10);a=ap.parse_args()
    begun=time.monotonic();attempts=0;unknown=0
    for fixed,p in candidates():
        attempts+=1;pairs=[]
        for roles in itertools.combinations(range(3),2):
            result=surround([fixed[i] for i in roles],a.seconds);result['roles']=roles;pairs.append(result)
            if result['status']!='SAT':
                unknown+=result['status']=='unknown';break
        if len(pairs)==3 and all(r['status']=='SAT' for r in pairs):
            all_covers=sorted(m.candidates({p},frozenset()))
            blockers=[{'placement':s,'roles':[i for i,t in enumerate(fixed) if m.cells(s)&m.cells(t)]} for s in all_covers]
            assert len(blockers)==27 and all(b['roles'] for b in blockers)
            data={'version':1,'status':'certified subset-minimal forbidden triple','scope':'No complete face/edge/vertex surround of the fixed core. Proper pairs have witnessed surrounds. Not an assertion that the raw packing overlaps, nor a new Heesch-number proof.',
                'fixed':fixed,'deadPoint':p,'coverBlockers':blockers,'pairs':pairs,'marking':synthesize(3),
                'search':{'attemptedTriples':attempts,'unknownPairQueries':unknown,'seconds':time.monotonic()-begun,'completeCatalogue':False},
                'finiteBoundaryRule':'Apply a learned obstruction in a finite-corona search only when its transformed dead point is an active required cell. An outer boundary hole need not be filled.'}
            out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,indent=2)+'\n')
            print(json.dumps({'status':data['status'],'fixed':fixed,'deadPoint':p,'marking':data['marking'],'search':data['search']}));return
        if attempts>=a.attempts:break
    raise SystemExit('Budget ended without a certified subset-minimal triple; status unknown.')
if __name__=='__main__':main()
