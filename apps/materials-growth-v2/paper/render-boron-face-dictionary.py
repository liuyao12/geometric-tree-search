"""Static scientific SVG of recovered finite template geometries, not artwork."""
import json
from pathlib import Path
import sys
import numpy as np
folder=Path(sys.argv[1]);d=json.loads((folder/'dictionary.json').read_text());cards=[]
angle=.55;elevation=.35
Rz=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
Rx=np.array([[1,0,0],[0,np.cos(elevation),-np.sin(elevation)],[0,np.sin(elevation),np.cos(elevation)]])
for i,t in enumerate(d['types']):
    c,o=next((c,o) for c in d['configurations'] for o in c['occurrences'] if o['type']==i)
    source=json.loads((folder/f"{c['fold']}-1.15-3.json").read_text());g=source['components'][o['component']]
    inverse={g['ids'][j]:u for u,j in enumerate(o['permutation'])};edges=[(inverse[a],inverse[b]) for a,b in g['edges']]
    x=np.array(t['positions']);_,_,axes=np.linalg.svd(x,full_matrices=False)
    if np.linalg.det(axes)<0:axes[-1]*=-1
    p=x@axes.T@Rz@Rx;p[:,:2]-=(p[:,:2].max(axis=0)+p[:,:2].min(axis=0))/2
    p*=160/max(np.ptp(p[:,:2],axis=0));p[:,0]+=185;p[:,1]=132-p[:,1]
    col=i%3;row=i//3;card=[f'<g transform="translate({20+col*390},{65+row*270})">',
        '<rect width="375" height="250" rx="12" fill="#f8fafc" stroke="#cbd5e1"/>',
        f'<text x="16" y="26" font-size="16" fill="#0f172a">T{i+1:02d} · {len(x)} sites</text>']
    for a,b in sorted(edges,key=lambda e:p[list(e),2].mean()):
        card.append(f'<line x1="{p[a,0]:.3f}" y1="{p[a,1]:.3f}" x2="{p[b,0]:.3f}" y2="{p[b,1]:.3f}" stroke="#64748b" stroke-width="1.5" opacity="0.65"/>')
    for a in np.argsort(p[:,2]):card.append(f'<circle cx="{p[a,0]:.3f}" cy="{p[a,1]:.3f}" r="4.5" fill="#d66aa5" stroke="#7b285b" stroke-width="0.6"/>')
    label='icosahedral graph' if o['icosahedralGraph'] else 'finite face-connected group'
    card.append(f'<text x="16" y="235" font-size="12" fill="#475569">{label}</text></g>');cards+=card
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200" role="img" aria-labelledby="title desc">'+\
    '<title id="title">Twelve recovered boron cluster templates</title><desc id="desc">Actual recovered atomic coordinates projected into separate panels. Seven twelve-site templates have icosahedral graphs. Other templates have fourteen, twenty-eight and twenty-nine sites.</desc>'+\
    '<rect width="1200" height="1200" fill="white"/><g font-family="Arial, sans-serif">'+\
    '<text x="20" y="30" font-size="23" fill="#0f172a">Geometry-only cluster proposals · six boron models</text>'+\
    '<text x="20" y="50" font-size="13" fill="#475569">No preferred motif size or polyhedron was supplied to the discovery algorithm.</text>'+''.join(cards)+\
    '<text x="20" y="1160" font-size="13" fill="#475569">Each panel is independently rescaled. Lines are geometric graph edges, not assigned chemical bonds.</text>'+\
    '<text x="20" y="1182" font-size="12" fill="#475569">Coordinates: An et al. (2016), supplementary CIF models. Finite proposals only; bridging pairs are not shown.</text></g></svg>'
with Path(sys.argv[2]).open('x') as out:out.write(svg)
