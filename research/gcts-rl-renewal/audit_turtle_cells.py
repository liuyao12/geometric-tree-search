"""Independent finite hypotheses for the written turtle region theorem.

No imports of turtle_cells, its driver, or search/proposal routines. Reconstructs
flags face-first using literal polygons; checks oriented boundary cancellation.
Pair interiors are compared by rational scanlines through every arrangement
band, independently of the producer's flag intersection predicate.
"""
import copy,hashlib,itertools,json,resource,time
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
POLYGON=((3,-2,-1),(2,0,-2),(0,1,-1),(0,2,-2),(-1,3,-2),(-2,2,0),
         (-1,0,1),(-2,0,2),(-2,-1,3),(0,-2,2),(1,-4,3),(2,-4,2),(3,-5,2),(4,-4,0))
SYMS=tuple((s,p) for s in (1,-1) for p in itertools.permutations(range(3)))
DIRS=((1,0),(0,1),(-1,1),(-1,0),(0,-1),(1,-1))
def det(a,b):return a[0]*b[1]-a[1]*b[0]
def minus(a,b):return tuple(x-y for x,y in zip(a,b))
def twice_area(p):return sum(det(a,b) for a,b in zip(p,p[1:]+p[:1]))
def contains(p,poly):
    # Open polygon membership; no numerical tolerance.
    x,y=p;crossings=0
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if det(minus(b,a),minus(p,a))==0 and all(min(a[d],b[d])<=p[d]<=max(a[d],b[d]) for d in (0,1)):return False
        if (a[1]>y)!=(b[1]>y) and x<a[0]+F((y-a[1])*(b[0]-a[0]),b[1]-a[1]):crossings+=1
    return crossings%2==1

def face_flags(poly):
    out={}
    # Bounds are expanded by two full lattice steps. A flag's owner differs
    # from every point of that flag by less than one coordinate unit.
    for x in range(min(p[0] for p in poly)-2,max(p[0] for p in poly)+2):
        for y in range(min(p[1] for p in poly)-2,max(p[1] for p in poly)+2):
            for face in (((x,y),(x+1,y),(x,y+1)),((x+1,y+1),(x,y+1),(x+1,y))):
                center=tuple(2*sum(p[d] for p in face) for d in (0,1))
                for p in face:
                    others=[q for q in face if q!=p];neighbors=[minus(q,p) for q in others]
                    i=next(i for i in range(6) if {DIRS[i],DIRS[(i+1)%6]}==set(neighbors))
                    for q in others:
                        s=0 if minus(q,p)==DIRS[i] else 1
                        t=((6*p[0],6*p[1]),tuple(3*(p[d]+q[d]) for d in (0,1)),center)
                        if twice_area(t)<0:t=(t[0],t[2],t[1])
                        midpoint=tuple(F(sum(v[d] for v in t),18) for d in (0,1))
                        if contains(midpoint,poly):out[(p[0],p[1],i,s)]=t
    return out

def boundary_check(poly,atoms):
    edges=Counter()
    for t in atoms.values():
        if twice_area(t)!=6:raise ValueError('invalid flag area')
        for a,b in zip(t,t[1:]+t[:1]):
            if edges[b,a]:edges[b,a]-=1
            else:edges[a,b]+=1
    polygon=tuple((6*p[0],6*p[1]) for p in poly)
    if twice_area(polygon)<0:polygon=tuple(reversed(polygon))
    covers=[[] for _ in polygon]
    for (a,b),v in edges.items():
        if not v:continue
        if v!=1:raise ValueError('atom boundary multiplicity')
        matched=False
        for j,(p,q) in enumerate(zip(polygon,polygon[1:]+polygon[:1])):
            d=minus(q,p)
            if det(d,minus(a,p)) or det(d,minus(b,p)):continue
            axis=0 if d[0] else 1;l=F(a[axis]-p[axis],d[axis]);r=F(b[axis]-p[axis],d[axis])
            if 0<=l<r<=1:covers[j].append((l,r));matched=True;break
        if not matched:raise ValueError('extra atom boundary or hole')
    for intervals in covers:
        prior=F(0)
        for l,r in sorted(intervals):
            if l!=prior:raise ValueError('boundary gap or overlap')
            prior=r
        if prior!=1:raise ValueError('omitted polygon side')
    if sum(twice_area(t) for t in atoms.values())!=twice_area(polygon):raise ValueError('area differs')
    return sum(len(c) for c in covers)

def transformed(poly,o,tr=(0,0,0)):
    s,perm=SYMS[o];return tuple(tuple(s*p[perm[d]]+tr[d] for d in range(3)) for p in poly)
def shifted(atoms,tr):return frozenset((x+tr[0],y+tr[1],i,s) for x,y,i,s in atoms)

def scanline_overlap(a,b):
    a=tuple(p[:2] for p in a);b=tuple(p[:2] for p in b)
    if any(max(p[d] for p in a)<=min(p[d] for p in b) or max(p[d] for p in b)<=min(p[d] for p in a) for d in (0,1)):return False,None,0
    heights={F(p[1]) for p in a+b}
    for p,q in zip(a,a[1:]+a[:1]):
        u=minus(q,p)
        for r,s in zip(b,b[1:]+b[:1]):
            v=minus(s,r);d=det(u,v)
            if not d:continue
            t=F(det(minus(r,p),v),d);z=F(det(minus(r,p),u),d)
            if 0<=t<=1 and 0<=z<=1:heights.add(F(p[1])+t*u[1])
    bands=0
    def intervals(poly,y):
        xs=sorted(F(p[0])+F((y-p[1])*(q[0]-p[0]),q[1]-p[1]) for p,q in zip(poly,poly[1:]+poly[:1]) if min(p[1],q[1])<y<max(p[1],q[1]))
        if len(xs)%2:raise ValueError('unpaired scanline crossings')
        return tuple(zip(xs[::2],xs[1::2]))
    ys=sorted(heights)
    for lo,hi in zip(ys,ys[1:]):
        y=(lo+hi)/2;bands+=1
        for l,r in intervals(a,y):
            for u,v in intervals(b,y):
                if max(l,u)<min(r,v):
                    x=(max(l,u)+min(r,v))/2
                    if not contains((x,y),a) or not contains((x,y),b):raise ValueError('bad overlap witness')
                    return True,[str(x),str(y)],bands
    return False,None,bands

def normal(x):return json.loads(json.dumps(x))
def canonical_hash(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()

def integer_tree(value):
    if type(value) is int:return
    if isinstance(value,(list,tuple)):
        for x in value:integer_tree(x)
        return
    if isinstance(value,dict):
        for x in value.values():integer_tree(x)
        return
    raise ValueError('finite geometry payload must use exact integers')

def check_pairs(records,expected,fingerprint):
    integer_tree(records)
    if normal(records)!=normal(expected):raise ValueError('pair catalog incomplete or changed')
    if fingerprint!=canonical_hash(expected):raise ValueError('pair fingerprint differs')

def hypotheses(data):
    integer_tree(data['vertices']);integer_tree(data['symmetries']);integer_tree(data['orientations'])
    if data['vertices']!=normal(POLYGON) or data['symmetries']!=normal(SYMS):raise ValueError('changed declared geometry')
    atoms=[];points=[];segments=0
    for o in range(12):
        poly=transformed(POLYGON,o);flags=face_flags(poly);segments+=boundary_check(poly,flags)
        actual=sorted(flags);counts=Counter((x,y,-x-y) for x,y,i,s in flags)
        if normal(actual)!=data['orientations'][o]['flags'] or normal(sorted(counts.items()))!=data['orientations'][o]['occupancy']:
            raise ValueError('changed atom or occupancy table')
        atoms.append(frozenset(flags));points.append(counts)
    # Actual search point values are checked only after the independent
    # geometry and counts have been reconstructed from literal outlines.
    from turtle import BASE,SYMMETRIES,VERTICES
    if POLYGON!=VERTICES or SYMS!=SYMMETRIES or points[0]!=BASE:raise ValueError('frozen search model differs')
    expected=[];scan_bands=overlaps=legal_contacts=0
    for o in range(12):
        poly=transformed(POLYGON,o)
        for x in range(min(p[0] for p in POLYGON)-max(p[0] for p in poly),max(p[0] for p in POLYGON)-min(p[0] for p in poly)+1):
            for y in range(min(p[1] for p in POLYGON)-max(p[1] for p in poly),max(p[1] for p in POLYGON)-min(p[1] for p in poly)+1):
                if (o,x,y)==(0,0,0):continue
                tr=(x,y,-x-y);shifted_values={(p[0]+x,p[1]+y,p[2]-x-y):v for p,v in points[o].items()}
                conflict=sorted(p for p,v in shifted_values.items() if points[0][p]+v>12)
                shared=sorted(atoms[0]&shifted(atoms[o],tr));shared_points=len(set(points[0])&set(shifted_values))
                overlap,witness,bands=scanline_overlap(POLYGON,transformed(POLYGON,o,tr));scan_bands+=bands;overlaps+=overlap
                if bool(conflict)!=overlap or bool(shared)!=overlap:raise ValueError('geometric faithfulness discrepancy')
                legal_contacts+=not conflict and bool(shared_points)
                expected.append({'pose':[o,list(tr)],'overloaded_points':conflict,'shared_flags':shared,'shared_positive_points':shared_points})
    check_pairs(data['pairs'],expected,data['pair_sha256'])
    for field,value in {'occupied_flags':240,'point_count':28,'coordinate_area':'20','flag_coordinate_area':'1/12','coordinate_scale':6}.items():
        if data['prototype'][field]!=value:raise ValueError('prototype summary differs')
    stats={'orientations':12,'occupied_flags_per_orientation':len(atoms[0]),'boundary_segments_checked':segments,
        'pair_cases':len(expected),'overlapping_pairs':overlaps,'capacity_legal_pairs':len(expected)-overlaps,
        'legal_point_contacts':legal_contacts,'scanline_bands':scan_bands,'pair_sha256':canonical_hash(expected)}
    return atoms,points,stats

def replay_regions(data,atoms,points):
    source=DOCS/data['region_source']['artifact']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=data['region_source']['sha256']:raise ValueError('source region artifact differs')
    d=json.loads(source.read_text());cases=[];boundaries={b['identity']:b for b in d['problems']}
    for i,r in enumerate(d['evaluation']):cases.append(('evaluation/'+str(i),r,boundaries[r['problem']]))
    for i,r in enumerate(d['movable_evaluation']):
        for j,a in enumerate(r['attempts']):cases.append(('movable/'+str(i)+'/'+str(j),a['result'],d['movable_families'][r['family']][j]))
    summaries=[];covered=0
    for path,r,b in cases:
        if r['status']!='finite_exact_region':continue
        def values(keys):
            out=Counter()
            for o,tr in keys:
                if type(o) is not int or not 0<=o<12 or any(type(x) is not int for x in tr) or sum(tr):raise ValueError('invalid source pose')
                for p,v in points[o].items():out[p[0]+tr[0],p[1]+tr[1],p[2]+tr[2]]+=v
            return out
        exterior=values(b['owned'])
        if len(b['exterior'])!=len(exterior) or exterior!={tuple(p):v for p,v in b['exterior']}:raise ValueError('exterior has no declared polygon realization')
        keys=r['state']['base_expansion'];totals=values(keys);occupied=set();unique=set()
        for o,tr in keys:
            k=o,tuple(tr)
            if k in unique:raise ValueError('duplicate source owner')
            unique.add(k);a=shifted(atoms[o],tr)
            if occupied&a:raise ValueError('source polygon overlap')
            occupied.update(a)
        if normal(sorted(totals.items()))!=r['state']['totals']:raise ValueError('source totals differ')
        required={tuple(p) for p in b['required']};allowed={tuple(p) for p in b['allowed']}
        cells={(p[0],p[1],i,s) for p in required for i in range(6) for s in range(2)}
        complete=all(totals[p]==12 for p in required)
        row={'path':path,'problem':b['identity'],'lane':r.get('lane',path.split('/')[0]),'tiles':len(keys),
            'occupied_flags':len(occupied),'required_points':len(required),'required_flags':len(cells),
            'missing_required_flags':len(cells-occupied),'extra_flags_outside_required':len(occupied-cells),
            'flags_outside_allowed':sum((x,y,-x-y) not in allowed for x,y,i,s in occupied),'point_complete':complete}
        if not complete or row['missing_required_flags'] or row['flags_outside_allowed']:raise ValueError('source continuous target or envelope fails')
        covered+=len(cells);summaries.append(row)
    if summaries!=data['regions']:raise ValueError('region interpretation differs')
    for r in data['regions']:
        for k,v in r.items():
            if k in ('path','problem','lane'):
                if type(v) is not str:raise ValueError('invalid region identifier')
            elif k=='point_complete':
                if type(v) is not bool:raise ValueError('invalid completion flag')
            elif type(v) is not int:raise ValueError('invalid region integer')
    return {'completed_regions':len(summaries),'required_flags_replayed':covered,'fixed_exterior_realizations_checked':len(cases)}

def main():
    start=time.monotonic();path=DOCS/'turtle-cells-001.json';d=json.loads(path.read_text())
    for name,sha in d['sources'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=sha:raise ValueError('source binding differs: '+name)
    if d['written_theorem']['artifact']!='turtle-faithfulness.html' or hashlib.sha256((DOCS/'turtle-faithfulness.html').read_bytes()).hexdigest()!=d['written_theorem']['sha256']:
        raise ValueError('written theorem binding differs')
    atoms,points,stats=hypotheses(d);stats.update(replay_regions(d,atoms,points))
    closed={(x,y,-x-y) for x in range(-5,6) for y in range(-5,6) if max(abs(x),abs(y),abs(x+y))<=5}
    expected_control={'required_points':len(closed),'radius':5,'coordinate_area':str(len(closed)),'tile_coordinate_area':'20',
        'area_remainder':len(closed)%20,'status':'analytic_area_obstruction',
        'scope':'required equals allowed hexagon; zero exterior; whole tile support contained; no GCTS search or new marking'}
    if d['closed_region_control']!=expected_control or not len(closed)%20:raise ValueError('closed area obstruction differs')
    stats['closed_area_obstructions']=1
    # Test meaningful omissions and altered finite hypotheses, without repeating
    # every scanline case for each mutation.
    mutations=[]
    for kind in ('vertex','symmetry','flag','occupancy','fractional-integer','boolean-integer'):
        bad=copy.deepcopy(d)
        if kind=='vertex':bad['vertices'][0][0]+=1
        elif kind=='symmetry':bad['symmetries'][0][0]=-1
        elif kind=='flag':bad['orientations'][0]['flags'].pop()
        elif kind=='occupancy':bad['orientations'][0]['occupancy'][0][1]+=1
        elif kind=='fractional-integer':bad['orientations'][0]['flags'][0][0]=float(bad['orientations'][0]['flags'][0][0])
        else:bad['orientations'][0]['flags'][0][3]=bool(bad['orientations'][0]['flags'][0][3])
        try:hypotheses(bad)
        except ValueError:mutations.append(kind)
        else:raise ValueError('changed finite hypothesis accepted')
    expected=d['pairs']
    for kind in ('pair-omission','pair-pose','pair-overlap','pair-capacity'):
        bad=copy.deepcopy(d['pairs'])
        if kind=='pair-omission':bad.pop()
        elif kind=='pair-pose':bad[0]['pose'][1][0]+=1
        elif kind=='pair-overlap':next(r for r in bad if r['shared_flags'])['shared_flags']=[]
        else:next(r for r in bad if r['overloaded_points'])['overloaded_points']=[]
        try:check_pairs(bad,expected,canonical_hash(bad))
        except ValueError:mutations.append(kind)
        else:raise ValueError('changed pair binding accepted')
    bad=copy.deepcopy(d);bad['regions'][0]['missing_required_flags']=1
    try:replay_regions(bad,atoms,points)
    except ValueError:mutations.append('region-coverage')
    else:raise ValueError('changed region accepted')
    stats.update(seconds=time.monotonic()-start,peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        tampered_records_rejected=len(mutations),mutations=mutations,audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='finite flag boundary and scanline checks plus old region replay; written universal theorem is analytic, not a formally checked proof or discovered infinite construction')
    d['independent_audit']=stats;path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps(stats,indent=2),flush=True)

if __name__=='__main__':main()
