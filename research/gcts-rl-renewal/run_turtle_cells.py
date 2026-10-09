"""Produce finite hypotheses for turtle polygon/point and region equivalence."""
import hashlib,json,resource,time
from collections import Counter
from pathlib import Path
from turtle import BASE,VERTICES,SYMMETRIES,transform
from turtle_cells import prototype,orientations,pair_catalog,verify_region,patch_flags

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=('turtle_cells.py','run_turtle_cells.py','turtle.py','audit_geometry.py')
def normal(x):return json.loads(json.dumps(x))
def main():
    start=time.monotonic();atoms,stats=prototype();oriented=orientations(atoms);pairs=pair_catalog(oriented)
    data={'vertices':VERTICES,'symmetries':SYMMETRIES,'coordinate_system':'first two A2 cube components; drawing uses an affine Euclidean projection',
        'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES},
        'method':'exact rational ear/convex clipping of every candidate flag; checked symmetry transfer; full relative-pose rectangle; inspection only',
        'prototype':stats,'written_theorem':{'artifact':'turtle-faithfulness.html','sha256':hashlib.sha256((DOCS/'turtle-faithfulness.html').read_bytes()).hexdigest(),
            'status':'analytic mathematical argument; not translated to the formal logical kernel'},
        'orientations':[{'flags':sorted(a),'occupancy':sorted((transform(p,g),v) for p,v in BASE.items())} for a,g in zip(oriented,SYMMETRIES)],
        'pairs':pairs,'pair_sha256':hashlib.sha256(json.dumps(pairs,separators=(',',':')).encode()).hexdigest(),
        'theorem_scope':'written analytic equivalence for this polygon, twelve A2 symmetries and integer A2 translations; independent finite hypotheses; no machine-checked soundness theorem, new search result, learned marking, or infinite construction'}
    source=DOCS/'conditional-clusters-001.json';parent=json.loads(source.read_text())
    data['region_source']={'artifact':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'reuse':'historical notebook 21 requests and declared exterior placements; no new solving or policy training'}
    problems={b['identity']:b for b in parent['problems']};cases=[]
    for i,r in enumerate(parent['evaluation']):cases.append(('evaluation/'+str(i),r,problems[r['problem']]))
    for i,r in enumerate(parent['movable_evaluation']):
        for j,a in enumerate(r['attempts']):cases.append(('movable/'+str(i)+'/'+str(j),a['result'],parent['movable_families'][r['family']][j]))
    rows=[]
    for path,r,b in cases:
        if r['status']!='finite_exact_region':continue
        _,exterior=patch_flags(b['owned'],oriented)
        if len(b['exterior'])!=len(exterior) or exterior!={tuple(p):v for p,v in b['exterior']}:raise ValueError('unrealized external point data')
        _,totals=patch_flags(r['state']['base_expansion'],oriented)
        if normal(sorted(totals.items()))!=r['state']['totals']:raise ValueError('historical totals differ')
        row=verify_region(r['state']['base_expansion'],b['required'],{tuple(p) for p in b['allowed']},oriented)
        if not row['point_complete'] or row['missing_required_flags'] or row['flags_outside_allowed']:raise ValueError('historical geometric region fails')
        rows.append(dict(path=path,problem=b['identity'],lane=r.get('lane',path.split('/')[0]),**row))
    data['regions']=rows
    data['closed_region_control']={'required_points':91,'radius':5,'coordinate_area':'91','tile_coordinate_area':'20',
        'area_remainder':11,'status':'analytic_area_obstruction',
        'scope':'required equals allowed hexagon; zero exterior; whole tile support contained; no GCTS search or new marking'}
    data['total_seconds']=time.monotonic()-start;data['peak_process_memory_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (DOCS/'turtle-cells-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(json.dumps({'prototype':stats,'pair_cases':len(pairs),'overlapping_pairs':sum(bool(r['shared_flags']) for r in pairs),
        'legal_point_contacts':sum(not r['overloaded_points'] and bool(r['shared_positive_points']) for r in pairs),
        'completed_regions':len(rows),'seconds':data['total_seconds'],'peak_process_memory_bytes':data['peak_process_memory_bytes']},indent=2),flush=True)

if __name__=='__main__':main()
