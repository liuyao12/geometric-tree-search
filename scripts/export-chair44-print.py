"""Export the exact centered Chair44 boundary as STL, 3MF and editable OpenSCAD.

Usage: NODE_BINARY=/path/to/node python3 scripts/export-chair44-print.py
       python3 scripts/export-chair44-print.py --width-mm 64 --output /tmp/print
Only scale and translation are changed; no smoothing or tolerance offset.
"""
import argparse, json, math, os, struct, subprocess, zipfile
from collections import defaultdict
from fractions import Fraction as Q
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--width-mm', type=Q, default=Q(48))
p.add_argument('--output', type=Path, default=ROOT/'3d-reptiles/chair/print')
a = p.parse_args()
assert a.width_mm > 0
source = "import {tetraBoundary,BOUNDARY_SCALE} from './3d-reptiles/chair/tetra-relief.js';console.log(JSON.stringify({boundary:tetraBoundary(),scale:BOUNDARY_SCALE}));"
data = json.loads(subprocess.check_output([os.environ.get('NODE_BINARY','node'),'--input-type=module','-e',source], cwd=ROOT, text=True))
vertices, triangles, lookup = [], [], {}
for f in data['boundary']:
    ids = []
    for v in f['vertices']:
        key = tuple(v)
        if key not in lookup:
            lookup[key] = len(vertices); vertices.append(key)
        ids.append(lookup[key])
    for i in range(1,len(ids)-1): triangles.append((ids[0],ids[i],ids[i+1]))

def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def audit(vs, ts):
    edges=defaultdict(list); planes=[]; volume6=0
    for i,t in enumerate(ts):
        aa,bb,cc=[vs[j] for j in t]; n=cross(sub(bb,aa),sub(cc,aa))
        assert any(n), 'Degenerate triangle'
        pivot=next(x for x in n if x)
        planes.append(tuple(Q(x)/pivot for x in (*n,dot(n,aa))))
        volume6+=dot(aa,cross(bb,cc))
        for u,v in zip(t,t[1:]+t[:1]): edges[tuple(sorted((u,v)))].append((i,u,v))
    assert all(len(e)==2 and e[0][1:]==e[1][1:][::-1] for e in edges.values()), 'Nonmanifold edge or bad winding'
    parent=list(range(len(ts)))
    def root(i):
        while parent[i]!=i: i=parent[i]
        return i
    for e in edges.values():
        i,j=e[0][0],e[1][0]
        if planes[i]==planes[j]: parent[root(j)]=root(i)
    # Single-cycle links exclude pinched vertices.
    for vertex in range(len(vs)):
        link=defaultdict(set)
        for t in ts:
            if vertex in t:
                u,v=[j for j in t if j!=vertex];link[u].add(v);link[v].add(u)
        assert link and all(len(x)==2 for x in link.values())
        seen=set();pending=[next(iter(link))]
        while pending:
            v=pending.pop()
            if v not in seen:seen.add(v);pending.extend(link[v]-seen)
        assert seen==set(link)
    assert len(vs)-len(edges)+len(ts)==2
    assert volume6>0
    return {'mesh_vertices':len(vs),'mesh_edges':len(edges),'triangles':len(ts),'planar_faces':len({root(i) for i in range(len(ts))}),'volume':Q(volume6,6)}

raw=audit(vertices,triangles)
assert raw['planar_faces']==98 and raw['triangles']==284
assert raw['volume']==7*data['scale']**3
minimum=[min(v[i] for v in vertices) for i in range(3)]
span=[max(v[i] for v in vertices)-minimum[i] for i in range(3)]
assert len(set(span))==1
factor=a.width_mm/span[0]
mm=[tuple((v[i]-minimum[i])*factor for i in range(3)) for v in vertices]
checked=audit(mm,triangles)
assert checked['planar_faces']==98
fmt=lambda x:format(float(x),'.12g')
width=fmt(a.width_mm)
name='chair44-centered-'+width+'mm'
a.output.mkdir(parents=True,exist_ok=True)

# STL: standard outward, counterclockwise vertex order. Coordinates are mm.
stl=bytearray(('Chair44 centered relief; millimeters; overall '+width+' mm').encode().ljust(80,b'\0'))
stl+=struct.pack('<I',len(triangles))
for t in triangles:
    vs=[mm[i] for i in t]; n=cross(sub(vs[1],vs[0]),sub(vs[2],vs[0]));length=math.sqrt(dot(n,n))
    stl+=struct.pack('<12fH',*(float(x)/length for x in n),*(float(x) for v in vs for x in v),0)
(a.output/(name+'.stl')).write_bytes(stl)

# 3MF Core: explicit units and one manifold object; deliberately no printer profile.
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',ns)
def tag(s):return '{'+ns+'}'+s
model=ET.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
ET.SubElement(model,tag('metadata'),{'name':'Title'}).text='Chair44 centered relief — '+width+' mm'
resources=ET.SubElement(model,tag('resources'))
obj=ET.SubElement(resources,tag('object'),{'id':'1','type':'model','name':'Chair44 centered relief'})
mesh=ET.SubElement(obj,tag('mesh'));verts=ET.SubElement(mesh,tag('vertices'))
for v in mm:ET.SubElement(verts,tag('vertex'),dict(zip(('x','y','z'),map(fmt,v))))
tris=ET.SubElement(mesh,tag('triangles'))
for t in triangles:ET.SubElement(tris,tag('triangle'),dict(zip(('v1','v2','v3'),map(str,t))))
ET.SubElement(ET.SubElement(model,tag('build')),tag('item'),{'objectid':'1'})
content_types=b'''<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'''
relationships=b'''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'''
def archive(path, entries):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for filename,body in entries.items():
            info=zipfile.ZipInfo(filename,date_time=(2026,9,27,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,body)
archive(a.output/(name+'.3mf'),{'[Content_Types].xml':content_types,'_rels/.rels':relationships,'3D/3dmodel.model':ET.tostring(model,encoding='utf-8',xml_declaration=True)})

# OpenSCAD uses clockwise ordering viewed from outside, opposite to STL/3MF.
points=[list(sub(v,minimum)) for v in vertices]
scad='// Chair44: centered apex (2,1,1) on the original side-3 cube.\n// Exact merged-cavity boundary: 98 planar faces, 284 mesh triangles.\n// Change overall_width_mm to resize uniformly; dimensions are millimeters.\n'
scad+='overall_width_mm = '+width+';\n'
scad+='points_lattice = '+json.dumps(points,separators=(',',':'))+';\n'
scad+='faces_clockwise = '+json.dumps([list(reversed(t)) for t in triangles],separators=(',',':'))+';\n'
scad+='scale(overall_width_mm/'+str(span[0])+')\n  polyhedron(points=points_lattice, faces=faces_clockwise, convexity=20);\n'
(a.output/'chair44-centered.scad').write_text(scad)

# Reopen both delivery meshes and re-audit the actual serialized coordinates.
reopened_stl=[];reopened_ts=[];dedup={}
assert len(stl)==84+50*len(triangles)
for i in range(struct.unpack_from('<I',stl,80)[0]):
    values=struct.unpack_from('<12fH',stl,84+50*i); ids=[]
    for j in (3,6,9):
        v=tuple(Q(x) for x in values[j:j+3])
        if v not in dedup:dedup[v]=len(reopened_stl);reopened_stl.append(v)
        ids.append(dedup[v])
    reopened_ts.append(tuple(ids))
stl_audit=audit(reopened_stl,reopened_ts)
with zipfile.ZipFile(a.output/(name+'.3mf')) as z:
    assert z.testzip() is None
    doc=ET.fromstring(z.read('3D/3dmodel.model'))
    rv=[tuple(Q(v.attrib[c]) for c in ('x','y','z')) for v in doc.findall('.//'+tag('vertex'))]
    rt=[tuple(int(t.attrib[c]) for c in ('v1','v2','v3')) for t in doc.findall('.//'+tag('triangle'))]
    mf_audit=audit(rv,rt)
assert stl_audit['planar_faces']==mf_audit['planar_faces']==98
assert abs(float(stl_audit['volume']/checked['volume'])-1)<1e-6
assert abs(float(mf_audit['volume']/checked['volume'])-1)<1e-9
report={k:(str(v) if isinstance(v,Q) else v) for k,v in checked.items()}
report.update(overall_dimensions_mm=[width]*3,small_cube_side_mm=fmt(data['scale']*factor),volume_mm3=fmt(checked['volume']),apex_original_units=[2,1,1],watertight=True,oriented=True,vertex_links_manifold=True,geometry='centered apex; touching cavities merged; no clearance offset',stl_roundtrip_verified=True,three_mf_roundtrip_verified=True)
(a.output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
readme=f'''# Chair44 print model

This is the current centered-pyramid relief, with apex \\((2,1,1)\\) for a base
triangle \\((0,0,0),(3,0,0),(3,3,0)\\). Touching dents are joined, and their
internal walls are removed. This is one solid part, not separate pyramids.

- **98 connected planar faces**, represented by **284 triangles**.
- Overall bounding box: \\({width} \\times {width} \\times {width}\\) mm.
- Small-cube side: \\({fmt(data['scale']*factor)}\\) mm.
- Geometric volume: \\({fmt(checked['volume'])}\\) cubic millimeters.
- Closed, consistently oriented surface with manifold vertex links.

## Files

- `{name}.3mf`: one model with explicit millimeter units, ready to import into a slicer.
- `{name}.stl`: the same mesh; select **millimeters** if asked for units.
- `chair44-centered.scad`: standalone editable OpenSCAD source. Change
  `overall_width_mm` to resize uniformly, then render and export.
- `verification.json`: mesh counts, dimensions, volume and round-trip checks.

Import the 3MF or STL into your slicer as a model. Choose the actual printer,
material, build orientation and support settings there; these files contain
no machine-specific G-code or slicer settings. The geometry includes undercuts
and pointed protrusions; review support placement and removal before printing.

This export preserves the exact ideal fit. It includes no added mating clearance;
print a small mating trial before ordering many copies. The CAD source changes
size only; it does not silently alter the apex or relief shape. Surface colors
from the web visualization are not included in these single-material files.

## Sliding and assembly

The exact exported geometry passes continuous straight-insertion checks for
all sixteen mating pairs in the canonical eight-tile supertile, with only two
copies present. Seven pairs have nonparallel faces that guide the final slide.
However, in the completed supertile every copy is locked against translation
when the other seven are fixed. One-at-a-time straight sliding cannot complete
that arrangement. Coordinated motion of all seven outer copies around the
fixed center has a verified geometric path; rotation-assisted insertion was
not tested. At the next level, eight rigid eight-tile supertiles are obstructed:
each outer cluster is translation-locked to the central cluster even as a pair,
so coordinated translation cannot assemble that level. This concerns assembled
clusters, not uniformly enlarged copies of this STL. These checks do not
establish assembly for arbitrary solver patches.

See the [assembly verification and reproducible tests](https://github.com/liuyao12/geometric-tree-search/blob/main/docs/projects/chair44-print-assembly.md).
These are ideal geometric checks; try two printed copies before ordering a set.

## Reproduction and verification

Run `NODE_BINARY=/path/to/node python3 scripts/export-chair44-print.py` from the
repository. Use `--width-mm` and `--output` for a different size or destination.
The exporter checks outward winding, paired edges, vertex links, connected
planar-face count and volume, then reopens the STL and 3MF and checks them again.
The separate `scripts/verify-chair-tetra-geometry.py` audits the exact boundary,
including the absence of coincident boundary-face patches.

Formats follow the [3MF Core specification](https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md)
and [OpenSCAD face-order convention](https://files.openscad.org/documentation/manual/Primitive_Solids.html).
'''
(a.output/'README.md').write_text(readme)
archive(a.output/'chair44-print-pack.zip',{f.name:f.read_bytes() for f in sorted(a.output.iterdir()) if f.name in [name+'.3mf',name+'.stl','chair44-centered.scad','verification.json','README.md']})
print(json.dumps(report,indent=2))
