#!/usr/bin/env python3
"""Additional nonperiodic-tiling benchmarks, with explicit unmarked geometries.

Matching rules/substitutions are metadata, not part of these scalar operators.
Only elementary functions with proved boundary parity enter the exact catalogue.
"""
from pathlib import Path
import hashlib
import json
import math
from elementary_modes import triangle_modes
from arithmetic_spectra import exact_mirrors, mv

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    basis = [[1,.5],[0,math.sqrt(3)/2]]
    group = exact_mirrors()['group_axial_matrices']
    domains = []
    specifications = [
        ('sphinx','Sphinx',[(0,0),(3,0),(2,1),(1,1),(0,2)],None,
         'The Sphinx admits hierarchical nonperiodic substitution tilings and also other tilings. Goodman–Strauss gives a marked tile system enforcing its substitution; the bare hexiamond is not claimed to force aperiodicity.',
         'https://arxiv.org/abs/2304.14388','https://arxiv.org/abs/1608.07168'),
        ('st-hexagon','Socolar–Taylor hexagon (bare geometry)',[(1,0),(0,1),(-1,1),(-1,0),(0,-1),(1,-1)],None,
         'The decorated Socolar–Taylor hexagon forces aperiodicity through nearest- and next-nearest-neighbor rules. Here the spectrum is that of the underlying regular hexagon; those rules have not been encoded in its boundary operator.',
         'https://arxiv.org/abs/1003.4279',None),
        ('pinwheel','Pinwheel triangle',None,[(0,0),(2,0),(0,1)],
         'Radin’s pinwheel substitution gives nonperiodic tilings with infinitely many tile orientations. The bare right triangle also tiles periodically by half-turn pairs.',
         'https://annals.math.princeton.edu/1994/139-3/p05',None),
        ('penrose-thick','Penrose thick rhombus',None,[(0,0),(1,0),(1+math.cos(2*math.pi/5),math.sin(2*math.pi/5)),(math.cos(2*math.pi/5),math.sin(2*math.pi/5))],
         'The thick and thin rhombi with Penrose matching rules form an aperiodic pair. Each bare rhombus is a parallelogram and tiles periodically; this operator does not yet encode the arrows.',
         'https://www.math.brown.edu/~res/M272/pentagrid.pdf',None),
        ('penrose-thin','Penrose thin rhombus',None,[(0,0),(1,0),(1+math.cos(math.pi/5),math.sin(math.pi/5)),(math.cos(math.pi/5),math.sin(math.pi/5))],
         'The thick and thin rhombi with Penrose matching rules form an aperiodic pair. Each bare rhombus is a parallelogram and tiles periodically; this operator does not yet encode the arrows.',
         'https://www.math.brown.edu/~res/M272/pentagrid.pdf',None),
        ('ammann-beenker','Ammann–Beenker rhombus',None,[(0,0),(1,0),(1+math.sqrt(.5),math.sqrt(.5)),(math.sqrt(.5),math.sqrt(.5))],
         'Beenker’s tetragrid construction gives nonperiodic tilings by a unit square and a rhombus with an acute angle of forty-five degrees. The bare rhombus tiles periodically. His simple arrow conditions alone do not force every tiling to be nonperiodic.',
         'https://pure.tue.nl/ws/files/4269555/253166.pdf',None),
    ]
    for identifier,label,axial,polygon,status,source,matching in specifications:
        if axial:
            polygon = [[p[0]+p[1]/2,p[1]*math.sqrt(3)/2] for p in axial]
        polygon = [list(p) for p in polygon]
        area = sum(p[0]*polygon[(i+1)%len(polygon)][1]-p[1]*polygon[(i+1)%len(polygon)][0] for i,p in enumerate(polygon))/2
        families,certificates = [],[]
        if axial:
            for i,p in enumerate(axial):
                e = tuple(axial[(i+1)%len(axial)][j]-p[j] for j in range(2))
                mirrors = [j for j,w in enumerate(group[6:]) if mv(w,e) == e]
                assert len(mirrors) == 1 and mirrors[0]%2 == 0
                w = group[6+mirrors[0]]
                certificates.append({'vertex':p,'edge':e,'group_index':6+mirrors[0],
                    'affine_translation':[p[j]-mv(w,p)[j] for j in range(2)]})
            for bc,short,long in [('D',-1,1),('N',1,1)]:
                signs,modes = triangle_modes(short,long)
                assert all(signs[c['group_index']] == (-1 if bc == 'D' else 1) for c in certificates)
                families.append({'bc':bc,'label':'Triangle: '+('Dirichlet' if bc == 'D' else 'Neumann')+' sides, even medians',
                    'source_kind':'triangle','source_boundary':[bc]*3,'median_boundary':'N',
                    'group_character':signs,'boundary_edges':[bc]*len(polygon),'modes':modes})
        else:
            families = [{'bc':'N','label':'Universal constant only','source_kind':'square','constant_only':True,
                'source_boundary':['N']*4,'boundary_edges':['N']*len(polygon),
                'modes':[{'id':'0:0','m':0,'n':0,'q':0,'normalized_value':0,'x_kind':'cos','y_kind':'cos','constructed_multiplicity':1}]}]
        domains.append({'id':identifier,'label':label,'polygon':polygon,'area':area,
            'lattice_basis':basis if axial else [[1,0],[0,1]],
            'lattice_vertices':axial,'boundary_certificates':certificates,
            'source_polygon':[[0,0],[1,0],[.5,math.sqrt(3)/2]] if axial else [[0,0],[1,0],[1,1],[0,1]],
            'families':families,'tiling_status':status,'source_url':source,'matching_source_url':matching})
    data = {'date':'2026-10-08','script_sha256':digest(Path(__file__)),
        'input_sha256':{name:digest(ROOT/name) for name in ['elementary_modes.py','arithmetic_spectra.py']},
        'group_axial_matrices':group,'domains':domains,
        'scope':'Bare polygon D/N spectra. Nonperiodicity belongs to the cited substitution, matching rules or cut-and-project construction. No scalar spectrum here is an aperiodicity test.'}
    (ROOT/'additional-tiles.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'additional_domains':len(domains),'exact_functions':sum(len(f['modes']) for d in domains for f in d['families'])}))


if __name__ == '__main__':
    main()
