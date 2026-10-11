#!/usr/bin/env python3
"""Independent geometry, matching-table, projection and publication checks.

This verifies the exact finite encoding and numerical artifacts, not a new
aperiodicity theorem, continuum eigenvalue enclosures or a substitution rule.
"""
from fractions import Fraction
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import math
import re
from PIL import Image

ROOT=Path(__file__).resolve().parent
PAGE=ROOT.parents[1]/'docs/projects/sphinx-boundary-modes.html'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(p,polygon):
    crossings=0
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>p[1]) != (b[1]>p[1]):
            x=Fraction(a[0])+Fraction(p[1]-a[1],b[1]-a[1])*(b[0]-a[0])
            crossings+=x>p[0]
    return crossings%2==1


class References(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.targets=[]
    def handle_starttag(self,tag,attributes):
        attributes=dict(attributes)
        if 'id' in attributes:self.ids.append(attributes['id'])
        for key in ('src','href'):
            if key in attributes:self.targets.append(attributes[key])


def main():
    construction=json.loads((ROOT/'sphinx-boundary-palette.json').read_text())
    projection=json.loads((ROOT/'sphinx-modal-projection.json').read_text())
    assert construction['status']==projection['status']=='passed'
    assert construction['script_sha256']==digest(ROOT/'sphinx_boundary_palette.py')
    assert projection['script_sha256']==digest(ROOT/'sphinx_modal_projection.py')
    for name,expected in projection['input_sha256'].items():assert digest(ROOT/name)==expected
    polygon=construction['geometry']['axial_polygon']
    assert polygon==[[0,0],[3,0],[2,1],[1,1],[0,2]]
    double_area=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(polygon,polygon[1:]+polygon[:1]))
    assert double_area==6
    cells={tuple(map(tuple,c)) for c in construction['geometry']['triangles']}
    assert len(cells)==6
    for cell in cells:
        centroid=tuple(sum(Fraction(p[i]) for p in cell)/3 for i in range(2))
        assert inside(centroid,polygon)
        a,b,c=cell
        assert abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))==1
    partner={tuple(sorted((3-a,2-b) for a,b in cell)) for cell in cells}
    target=set()
    for a in range(3):
        for b in range(2):
            target.add(tuple(sorted([(a,b),(a+1,b),(a,b+1)])))
            target.add(tuple(sorted([(a+1,b),(a+1,b+1),(a,b+1)])))
    assert not cells&partner and cells|partner==target
    collars=construction['collar_certificate']
    assert Fraction(collars['minimum_support_to_other_side_squared'])>Fraction(collars['collar_width'])**2
    assert Fraction(collars['minimum_between_supports_squared'])>=4*Fraction(collars['collar_width'])**2
    colors=construction['source_color_tuples_W_E_S_N'];states=construction['palette']
    assert len(colors)==11 and len(states)==22
    for i,(w,e,s,n) in enumerate(colors):
        i0=100+3*i
        a=[9+s,13+s,17+s,i0,i0+1,i0+2,5+w,1+w]
        b=[17+n,13+n,9+n,i0+2,i0+1,i0,1+e,5+e]
        assert states[2*i]['amplitudes']==a and states[2*i]['profile_direction']==1
        assert states[2*i+1]['amplitudes']==b and states[2*i+1]['profile_direction']==-1
    forced=construction['contact_audit']['forced_pairs']
    assert len(forced)==22
    for record in forced:
        root=record['root'];expected=('B' if root[0]=='A' else 'A')+root[1:]
        assert record['sole_connector_neighbor']=={'id':expected,'turn':3,'shift':[3,2]}
    expected=set()
    for i,(w,e,s,n) in enumerate(colors,1):
        for j,(W,E,S,N) in enumerate(colors,1):
            for shift,allowed in [((3,0),e==W),((-3,0),w==E),((0,2),n==S),((0,-2),s==N)]:
                if allowed:expected.add((i,j,0,shift))
    contacts=construction['contact_audit']['legal_contacts']
    actual={(c['left'],c['right'],c['turn'],tuple(c['shift'])) for c in contacts}
    assert actual==expected and len(actual)==len(contacts)==136
    assert construction['contact_audit']['tested_parallelogram_contacts']==13310
    assert construction['contact_audit']['rotated_or_staggered_legal_contacts']==0
    for run in projection['mesh_runs']:
        eigenvalues=run['eigenvalues']; assert len(eigenvalues)==180
        assert eigenvalues==sorted(eigenvalues) and eigenvalues[0]==0
        assert all(math.isfinite(v) for v in eigenvalues)
        assert run['diagnostics']['max_positive_relative_residual']<2e-12
        assert run['diagnostics']['max_mass_orthogonality_error']<1e-8
        assert len(run['states'])==22
        for record in run['states']:
            c=record['coefficients_first_180'];norm=record['sampled_target_squared_mass_norm']
            assert len(c)==180 and all(math.isfinite(v) for v in c) and norm>0
            last=0
            for truncation in record['truncations']:
                fraction=sum(v*v for v in c[:truncation['modes']])/norm
                assert abs(fraction-truncation['sampled_target_mass_fraction'])<1e-12
                assert last<=fraction<=1+1e-10;last=fraction
                assert abs(truncation['relative_sampled_mass_error']**2-(1-fraction))<1e-11
                assert math.isfinite(truncation['maximum_sampled_boundary_value_error_over_peak'])
    fine=projection['mesh_runs'][-1];spectrum=projection['eigenfunction_viewer']['domains'][0]['spectra'][0]
    assert [m['value'] for m in spectrum['modes']]==fine['eigenvalues']
    atlas=spectrum['atlas'];verified_cells=0
    for entry in atlas['pages']:
        path=ROOT/entry['file'];assert digest(path)==entry['sha256']
        with Image.open(path) as im:
            assert im.size==(atlas['columns']*atlas['cell_size'],entry['rows']*atlas['cell_size'])
            rgba=im.convert('RGBA')
            for local in range(entry['mode_count']):
                x,y=(local%atlas['columns'])*atlas['cell_size'],(local//atlas['columns'])*atlas['cell_size']
                box=(x,y,x+atlas['cell_size'],y+atlas['cell_size'])
                assert hashlib.sha256(rgba.crop(box).tobytes()).hexdigest()==atlas['cell_pixel_sha256'][entry['start_index']+local]
                verified_cells+=1
    assert verified_cells==180
    for figure in construction['figures']+[projection['atlas']]:assert digest(ROOT/figure['file'])==figure['sha256']
    source=PAGE.read_text();links=References();links.feed(source)
    assert len(links.ids)==len(set(links.ids))
    assert {'spectrum-viewer','spectrum-mode','spectrum-chart','spectrum-field',
            'palette-state','palette-field','palette-coefficient'}.issubset(links.ids)
    for link in links.targets:
        if link.startswith('#'):assert link[1:] in links.ids,link
        elif not link.startswith(('http:','https:','data:')):
            target=PAGE.parent/link.split('?')[0].split('#')[0]
            # This verifier creates its own linked receipt after all checks.
            if target.resolve()!=(ROOT/'sphinx-verification.json').resolve():assert target.exists(),link
    embedded=json.loads(re.search(r'<script id="mode-data" type="application/json">(.*?)</script>',source,re.S)[1])
    assert embedded==projection['eigenfunction_viewer']
    field_data=json.loads(re.search(r'<script id="palette-data" type="application/json">(.*?)</script>',source,re.S)[1])
    assert field_data['states']==states and field_data['projections']==fine['states']
    result={'date':'2026-10-11','status':'passed','states':22,'forced_mates':22,
        'audited_contacts':13310,'legal_contacts':136,'verified_eigenfunction_cells':verified_cells,
        'checks':['Exact axial polygon area and six fundamental triangles; complementary half-turn pair fills parallelogram',
            'Rational collar clearance inequalities and fixed state amplitude dictionaries',
            'Every recorded mate and full legal table compared with independent color adjacency',
            'Projection source hashes, finite coefficients, norm/error identities and two-mesh diagnostics',
            'All 180 numerical field pixels and figure hashes; embedded viewer data and local links'],
        'input_sha256':{p.name:digest(p) for p in [ROOT/'sphinx-boundary-palette.json',ROOT/'sphinx-modal-projection.json',ROOT/'sphinx-palette-viewer.js',PAGE]},
        'limitations':'Finite encoding and numerical consistency checks. Infinite existence/aperiodicity use the Jeandel--Rao theorem. No computed finite-mode tolerance cutoff, exact finite-mode equality, continuum error-enclosure or sphinx-substitution enforcement certificate.'}
    (ROOT/'sphinx-verification.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    assert (ROOT/'sphinx-verification.json').exists()
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','checks')},indent=2))


if __name__=='__main__':main()
