#!/usr/bin/env python3
"""Exact sphinx boundary-field construction and exhaustive contact audit.

A specialized continuum construction, not a GCTS search engine. The
aperiodicity includes fields; the underlying paired sphinx geometry repeats.
This construction encodes Jeandel--Rao, not the sphinx substitution.
"""
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent
COLORS = [(0,0,1,0),(0,3,2,1),(1,0,2,2),(1,1,0,2),(1,3,2,3),
          (3,0,1,1),(3,1,1,1),(3,1,2,2),(3,3,3,1),(2,2,1,0),(2,2,0,2)]
AXIAL_POLYGON = [(0,0),(3,0),(2,1),(1,1),(0,2)]
# Counterclockwise unit segments. Axial basis: (1,0), (1/2,sqrt(3)/2).
EDGES = [((0,0),(1,0)),((1,0),(2,0)),((2,0),(3,0)),
         ((3,0),(2,1)),((2,1),(1,1)),((1,1),(0,2)),
         ((0,2),(0,1)),((0,1),(0,0))]
DELTA = Fraction(1,8)


def physical(p):
    return (float(p[0]+p[1]/2),float(p[1])*math.sqrt(3)/2)


POLYGON = [physical(p) for p in AXIAL_POLYGON]


def add(a,b):
    return tuple(x+y for x,y in zip(a,b))


def subtract(a,b):
    return tuple(x-y for x,y in zip(a,b))


def rotate(p,k):
    a,b = p
    for _ in range(k % 6): a,b = -b,a+b
    return a,b


def triangle(i,j,down=False):
    return tuple(sorted([(i+1,j),(i+1,j+1),(i,j+1)] if down else
                        [(i,j),(i+1,j),(i,j+1)]))


CELLS = frozenset([triangle(i,0) for i in range(3)]+
                  [triangle(i,0,True) for i in range(2)]+[triangle(0,1)])


def palette():
    states = []
    for index,(w,e,s,n) in enumerate(COLORS,1):
        v = lambda c,r: 1+4*r+c
        h = lambda c,r: 9+4*r+c
        i0,i1,i2 = [100+3*(index-1)+j for j in range(3)]
        a = [h(s,0),h(s,1),h(s,2),i0,i1,i2,v(w,1),v(w,0)]
        b = [h(n,2),h(n,1),h(n,0),i2,i1,i0,v(e,0),v(e,1)]
        for role,amplitudes,direction in [('A',a,1),('B',b,-1)]:
            states.append({'id':f'{role}{index}','wang_id':index,'role':role,
                           'amplitudes':amplitudes,'profile_direction':direction})
    return states


def placement(state,turn=0,shift=(0,0)):
    edges = {}
    for (p,q),amplitude in zip(EDGES,state['amplitudes']):
        p,q = add(rotate(p,turn),shift),add(rotate(q,turn),shift)
        # The directed CCW tangent is an exact proxy for the outward normal;
        # the clockwise Euclidean quarter-turn commutes with all rotations.
        normal_proxy = subtract(q,p)
        direction = state['profile_direction']
        if p > q: p,q,direction = q,p,-direction
        edges[(p,q)] = (amplitude,direction,normal_proxy)
    cells = frozenset(tuple(sorted(add(rotate(p,turn),shift) for p in cell))
                      for cell in CELLS)
    return {'cells':cells,'edges':edges}


def legal_contact(left,right):
    if left['cells'] & right['cells']: return False
    shared = left['edges'].keys() & right['edges'].keys()
    if not shared: return False
    return all(left['edges'][e][:2] == right['edges'][e][:2] and
               left['edges'][e][2] == tuple(-x for x in right['edges'][e][2])
               for e in shared)


def pair(a,b):
    left,right = placement(a),placement(b,3,(3,2))
    assert legal_contact(left,right)
    cells = left['cells'] | right['cells']
    target = frozenset(triangle(i,j,d) for i in range(3) for j in range(2)
                       for d in (False,True))
    assert cells == target and len(cells) == 12
    shared = left['edges'].keys() & right['edges'].keys()
    assert len(shared) == 3
    return {'cells':cells,'edges':{e:v for member in (left,right)
                for e,v in member['edges'].items() if e not in shared}}


def transform(block,turn,shift=(0,0)):
    edges = {}
    for (p,q),(amplitude,direction,normal) in block['edges'].items():
        p,q = add(rotate(p,turn),shift),add(rotate(q,turn),shift)
        if p > q: p,q,direction = q,p,-direction
        edges[(p,q)] = (amplitude,direction,rotate(normal,turn))
    return {'cells':frozenset(tuple(sorted(add(rotate(p,turn),shift) for p in cell))
                             for cell in block['cells']),'edges':edges}


def contact_shifts(left,right):
    return {subtract(p,r) for p,q in left['edges'] for r,s in right['edges']
            if subtract(q,p) == subtract(s,r)}


def audit(states):
    forced = []
    for state in states:
        left = placement(state)
        amplitude = 100+3*(state['wang_id']-1)
        connector = next(e for e,v in left['edges'].items() if v[0] == amplitude)
        found = []
        for other in states:
            for turn in range(6):
                initial = placement(other,turn)
                for edge,v in initial['edges'].items():
                    if v[0] != amplitude or subtract(edge[1],edge[0]) != subtract(connector[1],connector[0]):
                        continue
                    shift = subtract(connector[0],edge[0])
                    if legal_contact(left,placement(other,turn,shift)):
                        found.append({'id':other['id'],'turn':turn,'shift':list(shift)})
        expected = ('B' if state['role']=='A' else 'A')+str(state['wang_id'])
        assert found == [{'id':expected,'turn':3,'shift':[3,2]}], (state,found)
        forced.append({'root':state['id'],'sole_connector_neighbor':found[0]})
    blocks = [pair(states[2*i],states[2*i+1]) for i in range(11)]
    tested,contacts = 0,[]
    for i,left in enumerate(blocks):
        for j,block in enumerate(blocks):
            for turn in range(6):
                initial = transform(block,turn)
                for shift in sorted(contact_shifts(left,initial)):
                    tested += 1
                    valid = legal_contact(left,transform(block,turn,shift))
                    w,e,s,n = COLORS[i]; W,E,S,N = COLORS[j]
                    expected = turn == 0 and ((shift == (3,0) and e == W) or
                        (shift == (-3,0) and w == E) or (shift == (0,2) and n == S) or
                        (shift == (0,-2) and s == N))
                    assert valid == expected, (i,j,turn,shift,valid,expected)
                    if valid: contacts.append({'left':i+1,'right':j+1,'turn':turn,'shift':list(shift)})
    return {'forced_pairs':forced,'tested_parallelogram_contacts':tested,
            'legal_contact_count':len(contacts),'legal_contacts':contacts,
            'rotated_or_staggered_legal_contacts':0}


def dot(a,b):
    return a[0]*b[0]+a[1]*b[1]+(a[0]*b[1]+a[1]*b[0])/2


def point_distance_squared(p,a,b):
    d = subtract(b,a)
    t = max(Fraction(0),min(Fraction(1),dot(subtract(p,a),d)/dot(d,d)))
    residual = subtract(p,add(a,tuple(t*x for x in d)))
    return dot(residual,residual)


def segment_distance_squared(a,b,c,d):
    # All segments are disjoint boundary segments or trimmed portions thereof;
    # no interior crossings occur in this simple polygon.
    return min(point_distance_squared(a,c,d),point_distance_squared(b,c,d),
               point_distance_squared(c,a,b),point_distance_squared(d,a,b))


def collar_certificate():
    edges = [(tuple(map(Fraction,p)),tuple(map(Fraction,q))) for p,q in EDGES]
    supports = [(add(p,tuple(x/4 for x in subtract(q,p))),
                 add(p,tuple(3*x/4 for x in subtract(q,p)))) for p,q in edges]
    clearance = min(segment_distance_squared(*supports[i],*edges[j])
                    for i in range(8) for j in range(8) if i != j)
    separation = min(segment_distance_squared(*supports[i],*supports[j])
                     for i in range(8) for j in range(i))
    assert clearance > DELTA**2 and separation >= (2*DELTA)**2
    return {'minimum_support_to_other_side_squared':str(clearance),
            'minimum_between_supports_squared':str(separation),
            'collar_width':str(DELTA),'normal_flux':'Exactly zero: K is even and K prime at zero is zero.'}


def bump(z):
    import numpy as np
    z = np.asarray(z,dtype=float); result = np.zeros_like(z)
    mask = abs(z)<1
    result[mask] = np.exp(1-1/(1-z[mask]**2))
    return result


def field_values(points,state):
    import numpy as np
    points = np.asarray(points,dtype=float); result = np.zeros(len(points))
    for (p,q),amplitude in zip(EDGES,state['amplitudes']):
        p,q = np.array(physical(p)),np.array(physical(q))
        tangent = q-p; outward = np.array([tangent[1],-tangent[0]])
        local = points-p
        s = local[:,0]*tangent[0]+local[:,1]*tangent[1]
        r = -(local[:,0]*outward[0]+local[:,1]*outward[1])
        result += amplitude*bump(4*(s-.5))*np.exp(2*state['profile_direction']*(s-.5))*bump(r/float(DELTA))
    assert np.all(np.isfinite(result))
    return result


def render(states):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.path import Path as PlotPath
    from matplotlib.patches import Polygon
    from matplotlib.colors import PowerNorm
    x,y = np.meshgrid(np.linspace(0,3,401),np.linspace(0,math.sqrt(3),251))
    points = np.column_stack([x.ravel(),y.ravel()])
    missing = ~PlotPath(POLYGON).contains_points(points,radius=1e-10).reshape(x.shape)
    values = [np.ma.array(field_values(points,s).reshape(x.shape),mask=missing) for s in states]
    peak = max(float(z.max()) for z in values)
    fig,axes = plt.subplots(6,4,figsize=(12,13))
    fig.subplots_adjust(left=.025,right=.88,bottom=.025,top=.935,hspace=.42,wspace=.25)
    for ax,state,z in zip(axes.flat,states,values):
        image = ax.imshow(z,origin='lower',extent=(0,3,0,math.sqrt(3)),cmap='viridis',norm=PowerNorm(.4,vmin=0,vmax=peak))
        ax.add_patch(Polygon(POLYGON,fill=False,lw=1.1)); ax.set_aspect('equal'); ax.axis('off')
        ax.set_xlim(-.2,3.2);ax.set_ylim(-.2,math.sqrt(3)+.2)
        ax.set_title(r'$%s_{%s}$'%(state['role'],state['wang_id']),fontsize=13)
        for (p,q),amplitude in zip(EDGES,state['amplitudes']):
            p,q = np.array(physical(p)),np.array(physical(q)); d = q-p
            label = (p+q)/2+.1*np.array([d[1],-d[0]])
            ax.text(*label,r'$%d$'%amplitude,ha='center',va='center',fontsize=7,
                    bbox={'facecolor':'white','edgecolor':'none','alpha':.8,'pad':.2})
    for ax in list(axes.flat)[22:]:ax.axis('off')
    fig.suptitle('Twenty-two field states on the same sphinx',fontsize=20,y=.985)
    fig.text(.5,.957,'Exact Neumann boundary carriers; infinite ordinary modal expansions',ha='center',fontsize=11)
    cax = fig.add_axes([.91,.22,.012,.54]);fig.colorbar(image,cax=cax).set_label(r'$u(x,y)$')
    atlas = ROOT/'sphinx-boundary-palette.png';fig.savefig(atlas,dpi=150,facecolor='white');plt.close(fig)
    fig,ax = plt.subplots(figsize=(10,5.8));ax.set_aspect('equal');ax.axis('off')
    second = [physical(subtract((3,2),p)) for p in AXIAL_POLYGON]
    for polygon,color,label,position in [(POLYGON,'#e7efec',r'$A_1$',(1.15,.48)),
            (second,'#f5ecd9',r'$B_1$',(2.85,1.25))]:
        ax.add_patch(Polygon(polygon,facecolor=color,edgecolor='#263b3d',lw=2));ax.text(*position,label,ha='center',fontsize=23)
    left,right = placement(states[0]),placement(states[1],3,(3,2))
    common = left['edges'].keys() & right['edges'].keys()
    for member in (left,right):
        for edge,(amplitude,direction,normal) in member['edges'].items():
            if edge in common and member is right:continue
            p,q = map(lambda p:np.array(physical(p)),edge)
            ax.plot([p[0],q[0]],[p[1],q[1]],color='#b46343' if edge in common else '#147b7b',lw=4)
            d = np.array(physical(normal)); midpoint=(p+q)/2+.15*np.array([d[1],-d[0]])
            ax.text(*midpoint,r'$%d$'%amplitude,ha='center',va='center',fontsize=13,
                    bbox={'facecolor':'white','edgecolor':'none','alpha':.85,'pad':1})
    ax.set_xlim(-.45,4.45);ax.set_ylim(-.35,math.sqrt(3)+.35)
    ax.set_title('Three connector traces force a pair of sphinxes',fontsize=16,pad=18)
    fig.tight_layout();pair_image=ROOT/'sphinx-boundary-forced-pair.png';fig.savefig(pair_image,dpi=160,facecolor='white');plt.close(fig)
    return [{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (atlas,pair_image)]


def main():
    import numpy as np
    states=palette(); evidence=audit(states); collars=collar_certificate(); maximum=0.
    for state in states:
        for (p,q),amplitude in zip(EDGES,state['amplitudes']):
            for s in [0,.19,.375,.5,.61,.82,1]:
                point=add(physical(p),tuple(s*x for x in subtract(physical(q),physical(p))))
                expected=amplitude*float(bump(4*(s-.5)))*np.exp(2*state['profile_direction']*(s-.5))
                maximum=max(maximum,abs(float(field_values([point],state)[0])-expected))
    assert maximum<1e-10
    output={'date':'2026-10-11','status':'passed','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'geometry':{'axial_polygon':AXIAL_POLYGON,'physical_polygon':POLYGON,'unit_edges_ccw':EDGES,'triangles':sorted(CELLS),'area':'3 sqrt(3) / 2'},
        'palette':states,'source_color_tuples_W_E_S_N':COLORS,'number_of_field_states':22,
        'source':'https://arxiv.org/html/1506.06492v4#S4.F4; Figure 4 and Theorem 3.',
        'allowed_placements':'Triangular-lattice translations and six multiples of sixty degrees; no reflections; fixed amplitudes.',
        'boundary_operator':'Ordinary homogeneous Neumann Laplacian on the exact sphinx polygon.',
        'collar_certificate':collars,'maximum_sample_trace_error':maximum,'contact_audit':evidence,
        'infinite_claim':'Forced pairs form an aligned parallelogram lattice. Trace equality is exactly Jeandel--Rao adjacency; its theorem supplies existence and excludes decorated translation periods.',
        'modal_status':'Infinitely many ordinary Neumann eigenmodes per state; H1 convergence preserves the exact traces. No finite-mode or single-eigenvalue result.',
        'limitations':['Aperiodicity includes the fields; erasing them leaves periodic sphinx pairs.',
            'The finite allowed field palette is essential; homogeneous Neumann conditions alone do not force aperiodicity.',
            'This is not an enforcement of the sphinx substitution.',
            'Reflections, other placements and arbitrary renormalizations are excluded.',
            'Static multiple-eigenvalue fields; no componentwise or time-dependent matching claim.',
            'No search engine is modified and no GCTS search conformance is claimed.'],
        'figures':render(states)}
    (ROOT/'sphinx-boundary-palette.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'passed','states':22,'tested_contacts':evidence['tested_parallelogram_contacts'],
                      'legal_contacts':evidence['legal_contact_count'],'collars':collars,'trace_error':maximum},indent=2))


if __name__=='__main__':main()
