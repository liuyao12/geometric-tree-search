#!/usr/bin/env python3
"""Independent exact geometry/contact checks and numerical artifact audit.

The infinite tiling theorem is a cited dependency, not proved by this audit.
"""
from fractions import Fraction
from html.parser import HTMLParser
from itertools import product
from pathlib import Path
import hashlib
import json
import math
import re

ROOT=Path(__file__).resolve().parent
PAGE=ROOT.parents[1]/'docs/projects/chair-boundary-modes.html'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def rotate(r,a):return tuple(sum(x*y for x,y in zip(row,a)) for row in r)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def signature(panel):return tuple(panel['arrow'])+tuple(panel['cubic'])


class References(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.targets=[]
    def handle_starttag(self,tag,attributes):
        attributes=dict(attributes)
        if 'id' in attributes:self.ids.append(attributes['id'])
        for key in ['src','href']:
            if key in attributes:self.targets.append(attributes[key])


def main():
    construction=json.loads((ROOT/'chair-boundary-field.json').read_text())
    projection=json.loads((ROOT/'chair-modal-projection.json').read_text())
    assert construction['status']==projection['status']=='passed'
    assert construction['script_sha256']==sha(ROOT/'chair_boundary_field.mjs')
    assert projection['script_sha256']==sha(ROOT/'chair_modal_projection.py')
    for data in [construction,projection]:
        for name,value in data['input_sha256'].items():assert sha(ROOT/name)==value
    cells={tuple(c) for c in construction['geometry']['cells']}
    assert cells==set(product([0,1],repeat=3))-{(1,1,1)}
    normals=[tuple((s if j==i else 0) for j in range(3)) for i in range(3) for s in [-1,1]]
    expected={(tuple(2*c[i]+1+n[i] for i in range(3)),n) for c in cells for n in normals if tuple(c[i]+n[i] for i in range(3)) not in cells}
    panels=construction['panels'];actual=set()
    for p in panels:
        normal=tuple(p['normal']);point=tuple(round(2*v) for v in p['center']);actual.add((point,normal))
        sigma={'red':1,'green':-1,'blue':0}[p['color']]
        assert tuple(p['polar'])==tuple(sigma*v for v in normal)
        assert tuple(p['cubic'])==cross(p['polar'],p['arrow'])
        assert dot(p['arrow'],normal)==0 and dot(p['arrow'],p['arrow'])==2
        assert tuple(v/2 for v in cross(p['arrow'],p['cubic']))==tuple(p['polar'])
    assert len(actual)==len(panels)==24 and actual==expected
    cert=construction['carrier_certificate']
    assert Fraction(cert['support_ball_radius_squared'])==Fraction(cert['tangential_radius'])**2+Fraction(cert['normal_half_width'])**2
    assert 4*Fraction(cert['support_ball_radius_squared'])<=Fraction(cert['minimum_distinct_centers_squared'])
    assert Fraction(cert['support_ball_radius_squared'])<Fraction(cert['minimum_center_to_other_panel_squared'])
    variants=[]
    for r in construction['model']['rotations']:
        assert dot(r[0],cross(r[1],r[2]))==1
        assert [[dot(a,b) for b in r] for a in r]==[[1,0,0],[0,1,0],[0,0,1]]
        rotated_cells={tuple(int(x+Fraction(1,2)) for x in rotate(r,[Fraction(v)-Fraction(1,2) for v in c])) for c in cells}
        rotated_panels=[]
        for p in panels:
            center=tuple(x+1 for x in rotate(r,[v-1 for v in p['center']]))
            rotated_panels.append({'point':tuple(round(2*v) for v in center),'normal':rotate(r,p['normal']),
                'arrow':rotate(r,p['arrow']),'cubic':rotate(r,p['cubic']),'color':p['color']})
        variants.append((rotated_cells,rotated_panels))
    assert len(variants)==24
    root_panels={tuple(round(2*v) for v in p['center']):p for p in panels};neighbors=set();cases=0
    for variant_id,(other_cells,other_panels) in enumerate(variants):
        for shift in product(range(-2,3),repeat=3):
            cases+=1;shifted_cells={tuple(c[i]+shift[i] for i in range(3)) for c in other_cells}
            if cells&shifted_cells:continue
            contacts=0;allowed=True
            for p in other_panels:
                point=tuple(p['point'][i]+2*shift[i] for i in range(3))
                if point not in root_panels:continue
                contacts+=1;q=root_panels[point]
                expected=tuple(p['arrow'])==tuple(q['arrow']) and sorted([p['color'],q['color']]) in [['blue','blue'],['green','red']]
                encoded=signature(p)==signature(q)
                assert expected==encoded;allowed&=encoded
                assert p['normal']==tuple(-v for v in q['normal'])
            if contacts and allowed:neighbors.add((variant_id,shift,contacts))
    records={(p['variantId'],tuple(p['origin']),p['contact_panels']) for p in construction['contact_audit']['neighbors']}
    assert records==neighbors and len(records)==44 and cases==3000
    # Re-evaluate the formula on every retained surface point, independently.
    points=projection['viewer']['points'];faces=projection['viewer']['triangles'];n=projection['mesh_runs'][-1]['subdivisions_per_unit']
    integers=[tuple(round(v*n) for v in p) for p in points]
    assert len(set(integers))==len(points)
    area=Fraction(0)
    for face in faces:
        a,b,c=[integers[i] for i in face];u=tuple(b[i]-a[i] for i in range(3));v=tuple(c[i]-a[i] for i in range(3));normal=cross(u,v)
        assert sum(abs(x) for x in normal)==1
        area+=Fraction(1,2*n*n)
    assert area==24
    for x,stored in zip(points,projection['viewer']['exact_target_surface_values']):
        value=0
        for p in panels:
            offset=[x[i]-p['center'][i] for i in range(3)];r=dot(offset,p['normal']);y=[offset[i]-r*p['normal'][i] for i in range(3)];rho=dot(y,y)
            if rho<1/16 and abs(r)<1/4:
                value+=math.exp(2-1/(1-16*rho)-1/(1-16*r*r))*(dot(y,p['arrow'])+16*rho*dot(y,p['cubic']))
        assert abs(value-stored)<1e-12
    for run in projection['mesh_runs']:
        values=run['eigenvalues'];coefficients=run['coefficients'];norm=run['sampled_target_squared_mass_norm']
        assert len(values)==len(coefficients)==60 and values==sorted(values) and values[0]==0
        assert all(math.isfinite(v) for v in values+coefficients)
        diag=run['diagnostics'];mesh_n=run['subdivisions_per_unit']
        assert diag['nodes']==(2*mesh_n+1)**3-mesh_n**3 and diag['tetrahedra']==42*mesh_n**3
        assert abs(diag['volume']-7)<1e-10 and diag['maximum_positive_relative_matrix_residual']<2e-13
        assert diag['maximum_mass_orthogonality_error']<1e-10 and abs(coefficients[0])<1e-10
        last=0
        for entry in run['truncations']:
            fraction=sum(c*c for c in coefficients[:entry['modes']])/norm
            assert abs(entry['sampled_squared_mass_fraction']-fraction)<1e-12
            assert last<=fraction<=1+1e-12;last=fraction
            assert abs(entry['relative_sampled_mass_error']**2-(1-fraction))<1e-10
        for control in run['cube_cosine_controls']:
            assert all(sum(v*v for v in m)==control['q'] for m in control['frequencies'])
            assert 0<=control['minimum_sampled_subspace_capture']<=1+1e-10
    coarse,fine=projection['mesh_runs']
    assert all(b<=a*(1+1e-8)+1e-8 for a,b in zip(coarse['eigenvalues'],fine['eigenvalues']))
    for first,second in zip(coarse['cube_cosine_controls'],fine['cube_cosine_controls']):
        assert second['minimum_sampled_subspace_capture']>.99
        assert second['minimum_sampled_subspace_capture']>first['minimum_sampled_subspace_capture']
        assert second['maximum_relative_eigenvalue_difference']<.03
        assert second['maximum_relative_eigenvalue_difference']<first['maximum_relative_eigenvalue_difference']
    assert len(projection['viewer']['surface_values'])==60
    for vector,peak in zip(projection['viewer']['surface_values'],projection['viewer']['full_nodal_peaks']):
        assert len(vector)==len(points) and all(math.isfinite(v) for v in vector) and peak>0
        assert max(abs(v) for v in vector)<=peak*(1+1e-10)
    page=PAGE.read_text();embedded=re.search(r'<script id="chair-field-data" type="application/json">(.*?)</script>',page,re.S)
    assert json.loads(embedded.group(1))==construction
    refs=References();refs.feed(page);assert len(refs.ids)==len(set(refs.ids))
    for target in refs.targets:
        if target.startswith(('https://','http://')):continue
        local=target.split('?',1)[0].split('#',1)[0]
        if local and not local.endswith('chair-field-verification.json'):assert (PAGE.parent/local).exists(),local
        if target.startswith('#'):assert target[1:] in refs.ids
    assert all(id in refs.ids for id in ['chair-spectrum','chair-mode','chair-exact-view','chair-numerical-view','chair-mode-detail'])
    result={'date':'2026-10-11','status':'passed','prototype_fields':1,'oriented_fields':24,'tile_pair_cases':cases,'legal_face_neighbors':44,
        'verified_numerical_surface_fields':60,'surface_area':'24','constant_mode_coefficient':'Exactly zero analytically; sampled coefficients also vanish numerically.',
        'sha256':{p.name:sha(p) for p in [PAGE,ROOT/'chair-field-viewer.js',ROOT/'chair-boundary-field.json',ROOT/'chair-modal-projection.json',Path(__file__)]},
        'limitations':'Finite transfer and numerical consistency checks. Infinite existence and aperiodicity use the cited Chair44 theorem. No field-erasure theorem, unrestricted registration, reflection transfer, exact finite sum or certified tolerance cutoff.'}
    (ROOT/'chair-field-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='sha256'},indent=2))


if __name__=='__main__':main()
