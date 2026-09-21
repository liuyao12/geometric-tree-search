#!/usr/bin/env python3
"""Sample period lattices from patches, then solve each COMPLETE voxel quotient.

A SAT witness is an infinite periodic grid construction. UNSAT concerns only
that period lattice; a bounded proposal pool cannot establish aperiodicity.
"""
import argparse,hashlib,json,math,time
from collections import Counter,defaultdict
from itertools import combinations,permutations,product
from pathlib import Path
from threading import Timer
from pysat.solvers import Glucose3
from pysat import __version__ as pysat_version

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def det(b):return dot(b[0],cross(b[1],b[2]))
def extended_gcd(a,b):
    aa,bb=abs(a),abs(b);u,v,s,t=1,0,0,1
    while bb:q=aa//bb;aa,bb=bb,aa-q*bb;u,s=s,u-q*s;v,t=t,v-q*t
    return aa,u if a>=0 else -u,v if b>=0 else -v

def hnf(basis):
    if len(basis)!=3 or any(len(v)!=3 or any(type(x) is not int for x in v) for v in basis) or not det(basis):raise ValueError('Expected nonsingular integer basis')
    b=[list(v) for v in basis]
    for row in [2,1,0]:
        for j in range(row):
            a,c=b[row][row],b[j][row]
            if not c:continue
            g,u,v=extended_gcd(a,c);left,right=b[row][:],b[j][:]
            b[row]=[u*x+v*y for x,y in zip(left,right)]
            b[j]=[-(c//g)*x+(a//g)*y for x,y in zip(left,right)]
        if b[row][row]<0:b[row]=[-x for x in b[row]]
        for j in range(row+1,3):
            q=b[j][row]//b[row][row];b[j]=[x-q*y for x,y in zip(b[j],b[row])]
    return tuple(map(tuple,b))

def reduce_site(p,b):
    q=list(p)
    for i in [2,1,0]:
        n=q[i]//b[i][i];q=[x-n*y for x,y in zip(q,b[i])]
    return tuple(q)

def rotations():
    for perm in permutations(range(3)):
        parity=(-1)**sum(perm[i]>perm[j] for i in range(3) for j in range(i+1,3))
        for signs in product([-1,1],repeat=3):
            if parity*math.prod(signs)==1:yield perm,signs
ROTATIONS=list(rotations())
def rotated(p,r):return tuple(r[1][i]*p[r[0][i]] for i in range(3))
def normal(cells):
    low=[min(p[i] for p in cells) for i in range(3)]
    return tuple(sorted(tuple(p[i]-low[i] for i in range(3)) for p in cells))
def orientation_audit(voxels,orientations):
    if not voxels or len(set(map(tuple,voxels)))!=len(voxels) or any(len(v)!=3 or any(type(x) is not int for x in v) for v in voxels):raise ValueError('Invalid voxel tile')
    expected={normal([rotated(p,r) for p in voxels]) for r in ROTATIONS}
    if any(any(len(v)!=3 or any(type(x) is not int for x in v) for v in o) for o in orientations):raise ValueError('Invalid orientation coordinates')
    actual={normal(o) for o in orientations}
    if len(actual)!=len(orientations) or actual!=expected or any(len(o)!=len(voxels) for o in orientations):raise ValueError('Incomplete proper-rotation orientation table')

def quotient_pool(voxels,orientations,basis):
    orientation_audit(voxels,orientations);b=hnf(basis);volume=det(b)
    if volume%len(voxels):raise ValueError('Period volume is not a multiple of tile volume')
    sites=list(product(range(b[0][0]),range(b[1][1]),range(b[2][2])));indices={q:i for i,q in enumerate(sites)}
    pool=[];roots=set()
    for oi,o in enumerate(orientations):
        for t in sites:
            covered=tuple(sorted(indices[reduce_site(tuple(v[i]+t[i] for i in range(3)),b)] for v in o))
            if len(set(covered))!=len(voxels):continue
            # Keep placement identities, even when their quotient occupancies
            # coincide: relative-pair constraints depend on orientation/anchor.
            pool.append({'oi':oi,'translation':t,'sites':covered})
            if t==(0,0,0):roots.add(len(pool))
    return b,pool,roots

def replay_period(orientations,basis,placements,tile_volume):
    volume=abs(det(basis));by_key={';'.join(','.join(map(str,v)) for v in normal(o)):normal(o) for o in orientations};numerators=[cross(basis[1],basis[2]),cross(basis[2],basis[0]),cross(basis[0],basis[1])];seen=set()
    if volume!=len(placements)*tile_volume:return False
    for p in placements:
        for v in by_key[p['orientation_key']] if 'orientation_key' in p else orientations[p['orientation_index']]:
            q=[v[i]+p['translation'][i] for i in range(3)];key=tuple(dot(q,n)%volume for n in numerators)
            if key in seen:return False
            seen.add(key)
    return len(seen)==volume

def pair_constraint_edges(pool,basis,templates):
    lookup={(p['oi'],p['translation']):v for v,p in enumerate(pool,1)};edges=set()
    for a,b,delta in templates:
        if type(a) is not int or type(b) is not int or len(delta)!=3 or any(type(x) is not int for x in delta) or a==b and not any(delta):raise ValueError('Invalid relative pair')
        for v,p in enumerate(pool,1):
            if p['oi']!=a:continue
            t=reduce_site([p['translation'][i]+delta[i] for i in range(3)],basis);other=lookup.get((b,t))
            if other is not None:edges.add(tuple(sorted((v,other))))
    return edges

def certificate_templates(bundle,checker,orientations):
    from verify_voxel_pair_certificate import verify,normalized,rotations,rotate
    receipt=verify(bundle,checker);data=json.loads((bundle/'pair.input.json').read_text());old=[o['voxels'] for o in data['model']['orientations']]
    lookup={normalized(o)[0]:(i,normalized(o)[1]) for i,o in enumerate(orientations)}
    if set(lookup)!={normalized(o)[0] for o in old}:raise ValueError('Pair certificate is for another tile')
    templates=set()
    for r in rotations():
        transformed=[]
        for p in data['pair']:
            shape,origin=normalized(rotate(old[p['oi']],p['translation'],r));oi,offset=lookup[shape]
            transformed.append((oi,tuple(origin[i]-offset[i] for i in range(3))))
        for a,b in [transformed,transformed[::-1]]:templates.add((a[0],b[0],tuple(b[1][i]-a[1][i] for i in range(3))))
    receipt['manifestSha256']=hashlib.sha256((bundle/'manifest.json').read_bytes()).hexdigest()
    receipt['verifierSha256']=hashlib.sha256(Path(__file__).with_name('verify_voxel_pair_certificate.py').read_bytes()).hexdigest()
    receipt['checkerSha256']=hashlib.sha256(checker.read_bytes()).hexdigest()
    return sorted(templates),receipt

def solve_quotient(voxels,orientations,basis,time_ms=5000,origin_symmetry=True,pair_exclusions=()):
    if type(time_ms) is not int or time_ms<1:raise ValueError('Invalid time budget')
    start=time.perf_counter();deadline=start+time_ms/1000;b,pool,roots=quotient_pool(voxels,orientations,basis);volume=det(b)
    clauses=[];by_site=[[] for _ in range(volume)];variables=len(pool)
    for v,p in enumerate(pool,1):
        for q in p['sites']:by_site[q].append(v)
    for vs in by_site:
        clauses.append(vs)
        if len(vs)<6:clauses.extend([-a,-c] for a,c in combinations(vs,2))
        else:
            variables+=1;previous=variables;clauses.append([-vs[0],previous])
            for v in vs[1:-1]:
                variables+=1;current=variables;clauses.extend([[-v,current],[-previous,current],[-v,-previous]]);previous=current
            clauses.append([-vs[-1],-previous])
    # Any periodic tiling can be translated to put some tile's anchor at zero.
    # Its orientation is NOT fixed: the period lattice need not preserve rotations.
    if origin_symmetry:clauses.append(sorted(roots))
    edges=pair_constraint_edges(pool,b,pair_exclusions);clauses.extend(sorted(set([-a,-c])) for a,c in sorted(edges))
    stats={'backend':'glucose3','solverVersion':'python-sat '+pysat_version,'candidatePlacements':len(pool),'quotientSites':volume,'variables':variables,'clauses':len(clauses),'originSymmetry':origin_symmetry,'pairExclusionClauses':len(edges),'preparationMs':(time.perf_counter()-start)*1000}
    result={'basis':b,'copies':volume//len(voxels),'status':'unknown','certificate':None}
    if time.perf_counter()<deadline:
        with Glucose3(bootstrap_with=clauses) as solver:
            remaining=deadline-time.perf_counter()
            if remaining>0:
                timer=Timer(max(.001,remaining),solver.interrupt);timer.daemon=True;timer.start()
                try:answer=solver.solve_limited(expect_interrupt=True)
                finally:timer.cancel();timer.join();solver.clear_interrupt()
                if answer is False:result['status']='unsat_restricted_quotient' if pair_exclusions else 'unsat_period_lattice'
                if answer is True:
                    assignment=set(solver.get_model());selected=[{'orientation_index':p['oi'],'translation':p['translation']} for v,p in enumerate(pool,1) if v in assignment]
                    if not replay_period(orientations,b,selected,len(voxels)):raise AssertionError('Independent Cramer quotient replay failed')
                    for p in selected:
                        o=orientations[p['orientation_index']];p['orientation_key']=';'.join(','.join(map(str,v)) for v in normal(o))
                        p['translation']=[p['translation'][i]+min(v[i] for v in o) for i in range(3)]
                    result.update(status='periodic_certificate',certificate={'certified':True,'can_tile':True,'copies':len(selected),'period_vectors':b,'placements':selected})
    stats['elapsedMs']=(time.perf_counter()-start)*1000
    return {**result,'stats':stats,'scope':'Complete placement pool for this period lattice, with supplied relative pair restrictions if present; nonreference SAT scheduling. Unknown at a budget limit.'}

def propose_bases(patches,tile_volume,max_vectors=64,min_copies=1,max_copies=64):
    counts=Counter()
    for patch in patches:
        for a,b in combinations(patch,2):
            if a['oi']!=b['oi']:continue
            delta=[x-y for x,y in zip(a['translation'],b['translation'])]
            if len(delta)!=3 or any(type(x) is not int or x%2 for x in delta):raise ValueError('Expected half-unit coordinates and integer translations')
            v=tuple(x//2 for x in delta)
            if not any(v):continue
            if next(x for x in v if x)<0:v=tuple(-x for x in v)
            counts[v]+=1
    ranked=sorted(counts,key=lambda v:(-counts[v],dot(v,v),v))[:max_vectors];canonical={};proposals={};eligible=0
    for basis in combinations(ranked,3):
        volume=abs(det(basis))
        if not volume or volume%tile_volume or not min_copies<=volume//tile_volume<=max_copies:continue
        eligible+=1;normal_basis=hnf(basis)
        if normal_basis not in canonical:canonical[normal_basis]=min(hnf([rotated(v,r) for v in normal_basis]) for r in ROTATIONS)
        b=canonical[normal_basis];score=(min(counts[v] for v in basis),sum(counts[v] for v in basis),-sum(dot(v,v) for v in basis))
        if b not in proposals or score>proposals[b]['score']:proposals[b]={'basis':b,'copies':volume//tile_volume,'score':score,'sourceVectors':basis}
    return sorted(proposals.values(),key=lambda p:(tuple(-x for x in p['score']),p['copies'],p['basis'])),{'vectors':len(counts),'selectedVectors':len(ranked),'eligibleTriples':eligible,'uniqueLatticesUpToRotation':len(proposals)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--tile',required=True);p.add_argument('--output',required=True);p.add_argument('--time-ms',type=int,default=5000);p.add_argument('--max-vectors',type=int,default=64);p.add_argument('--max-bases',type=int,default=24);p.add_argument('--min-copies',type=int,default=1);p.add_argument('--max-copies',type=int,default=64);p.add_argument('--pair-certificate',type=Path);p.add_argument('--checker',type=Path);p.add_argument('--skip-report',type=Path,action='append',default=[]);a=p.parse_args()
    if min(a.max_vectors,a.max_bases,a.min_copies,a.time_ms)<1 or a.max_copies<a.min_copies:p.error('Invalid bounds')
    raw=Path(a.input).read_bytes();data=json.loads(raw);m=data['models'][a.tile];orientations=[o['voxels'] for o in m['orientations']];voxels=orientations[0]
    if m.get('allowReflections'):p.error('Proper rotations only')
    orientation_audit(voxels,orientations)
    started=time.perf_counter();templates=[];proof=None;proof_start=started
    if a.pair_certificate:
        if not a.checker:p.error('--pair-certificate requires --checker')
        templates,proof=certificate_templates(a.pair_certificate,a.checker,orientations)
    proof_ms=(time.perf_counter()-proof_start)*1000 if proof else 0
    proposals,stats=propose_bases([c['placements'] for c in data['cases'] if c['tile']==a.tile],len(voxels),a.max_vectors,a.min_copies,a.max_copies)
    skipped=set();skip_sources=[]
    for path in a.skip_report:
        raw_skip=path.read_bytes();old=json.loads(raw_skip)
        if old['tile']!=a.tile:p.error('Skip report belongs to another tile')
        skipped.update(hnf(row['basis']) for row in old['rows']);skip_sources.append({'path':str(path),'sha256':hashlib.sha256(raw_skip).hexdigest()})
    selected=[row for row in proposals if row['basis'] not in skipped][:a.max_bases]
    root=Path(__file__).resolve();report={'tile':a.tile,'inputSha256':hashlib.sha256(raw).hexdigest(),'sourceSha256':hashlib.sha256(root.read_bytes()).hexdigest(),'bounds':{k:[str(x) for x in v] if isinstance(v,list) else str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},'pairConstraintProof':proof,'proofPreparationMs':proof_ms,'skippedReports':skip_sources,'skippedProposals':sum(row['basis'] in skipped for row in proposals),'proposalStats':stats,'proposals':proposals,'rows':[],'scope':'Patch-derived sampled period lattices with complete quotient searches. Missing a certificate is not an aperiodicity or non-tiling proof.'}
    def save():
        report['elapsedMs']=(time.perf_counter()-started)*1000;Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
    save()
    for proposal in selected:
        r=solve_quotient(voxels,orientations,proposal['basis'],a.time_ms,pair_exclusions=templates)
        if proof and r['status']=='unsat_restricted_quotient':r['status']='unsat_period_lattice';r['proofBackedPairConstraints']=True
        report['rows'].append(r);save();print(json.dumps(r),flush=True)
        if r['certificate']:break
