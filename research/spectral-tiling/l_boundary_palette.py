#!/usr/bin/env python3
"""Only L-triominoes: exact scalar traces force pairs and an aperiodic palette.

This is a specialized continuum construction and exhaustive contact audit,
not a GCTS tiling/search engine. No finite patch supplies the infinite claim.
Smooth Neumann fields have infinite expansions in the ordinary L spectrum.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
# Jeandel--Rao arXiv:1506.06492v4, Figure 4; W,E,S,N.
COLORS = [(0,0,1,0),(0,3,2,1),(1,0,2,2),(1,1,0,2),(1,3,2,3),
          (3,0,1,1),(3,1,1,1),(3,1,2,2),(3,3,3,1),(2,2,1,0),(2,2,0,2)]
CELLS = frozenset([(0,0),(1,0),(0,1)])
# Unit edges, endpoints in increasing coordinate order, outward normals.
EDGES = [((0,0),(1,0),(0,-1)),((1,0),(2,0),(0,-1)),
         ((2,0),(2,1),(1,0)),((1,1),(2,1),(0,1)),
         ((1,1),(1,2),(1,0)),((0,2),(1,2),(0,1)),
         ((0,1),(0,2),(-1,0)),((0,0),(0,1),(-1,0))]
POLYGON = [(0,0),(2,0),(2,1),(1,1),(1,2),(0,2),(0,0)]
DELTA = 1/8


def rotate(p, k):
    x, y = p
    return [(x,y),(-y,x),(-x,-y),(y,-x)][k % 4]


def add(a, b):
    return tuple(x+y for x,y in zip(a,b))


def subtract(a, b):
    return tuple(x-y for x,y in zip(a,b))


def vertical(c, position):
    return 1+4*position+c


def horizontal(c, position):
    return 9+4*position+c


def palette():
    states = []
    for index, (w,e,s,n) in enumerate(COLORS):
        i0, i1, i2 = [100+3*index+j for j in range(3)]
        a = [horizontal(s,0),horizontal(s,1),i0,i1,i2,horizontal(n,0),vertical(w,1),vertical(w,0)]
        b = [horizontal(n,2),horizontal(n,1),i2,i1,i0,horizontal(s,2),vertical(e,0),vertical(e,1)]
        states.extend([{'id':f'A{index+1}','wang_id':index+1,'role':'A','amplitudes':a,'profile_direction':1},
                       {'id':f'B{index+1}','wang_id':index+1,'role':'B','amplitudes':b,'profile_direction':-1}])
    return states


def placement(state, turn=0, shift=(0,0)):
    edges = {}
    for (p,q,normal), amplitude in zip(EDGES, state['amplitudes']):
        p, q = add(rotate(p,turn),shift), add(rotate(q,turn),shift)
        direction = state['profile_direction']
        if p > q:
            p, q, direction = q, p, -direction
        edges[(p,q)] = (amplitude,direction,rotate(normal,turn))
    cells = frozenset(add(rotate((x,y),turn),shift) for x,y in CELLS)
    # Rotations act on the entire unit cell, not just its lower-left corner.
    corrections = [(0,0),(-1,0),(-1,-1),(0,-1)]
    cells = frozenset(add(c,corrections[turn % 4]) for c in cells)
    return {'cells':cells,'edges':edges}


def contact_shifts(left, right):
    shifts = set()
    for p,q in left['edges']:
        for r,s in right['edges']:
            if subtract(q,p) == subtract(s,r):
                shifts.add(subtract(p,r))
    return shifts


def legal_contact(left, right):
    if left['cells'] & right['cells']:
        return False
    common = left['edges'].keys() & right['edges'].keys()
    if not common:
        return False
    return all(left['edges'][edge][:2] == right['edges'][edge][:2]
               and left['edges'][edge][2] == tuple(-x for x in right['edges'][edge][2])
               for edge in common)


def pair(state_a, state_b):
    a, b = placement(state_a), placement(state_b,2,(3,2))
    assert not a['cells'] & b['cells']
    assert a['cells'] | b['cells'] == frozenset((x,y) for x in range(3) for y in range(2))
    shared = a['edges'].keys() & b['edges'].keys()
    assert len(shared) == 3 and legal_contact(a,b)
    return {'cells':a['cells'] | b['cells'],
            'edges':{edge:value for member in [a,b] for edge,value in member['edges'].items() if edge not in shared}}


def transform_block(block, turn=0, shift=(0,0)):
    edges = {}
    for (p,q),(amplitude,direction,normal) in block['edges'].items():
        p,q = add(rotate(p,turn),shift),add(rotate(q,turn),shift)
        if p > q:
            p,q,direction = q,p,-direction
        edges[(p,q)] = (amplitude,direction,rotate(normal,turn))
    correction = [(0,0),(-1,0),(-1,-1),(0,-1)][turn]
    cells = frozenset(add(add(rotate(c,turn),correction),shift) for c in block['cells'])
    return {'cells':cells,'edges':edges}


def audit(states):
    forced = []
    for root in states:
        left = placement(root)
        connector = 100+3*(root['wang_id']-1)
        edge = next(edge for edge,value in left['edges'].items() if value[0] == connector)
        candidates = []
        for other in states:
            for turn in range(4):
                initial = placement(other,turn)
                for segment,value in initial['edges'].items():
                    if value[0] != connector or subtract(segment[1],segment[0]) != subtract(edge[1],edge[0]):
                        continue
                    shift = subtract(edge[0],segment[0])
                    joined = placement(other,turn,shift)
                    if legal_contact(left,joined):
                        candidates.append({'id':other['id'],'turn':turn,'shift':list(shift)})
        expected_id = ('B' if root['role']=='A' else 'A')+str(root['wang_id'])
        assert candidates == [{'id':expected_id,'turn':2,'shift':[3,2]}], (root,candidates)
        forced.append({'root':root['id'],'sole_connector_neighbor':candidates[0]})

    blocks = [pair(states[2*i],states[2*i+1]) for i in range(11)]
    contacts, tested = [], 0
    # Exhaust all edge-sharing translations and all four relative rotations.
    # The integer/profile-direction labels are exact trace equality semantics.
    for i,left in enumerate(blocks):
        for j,block in enumerate(blocks):
            for turn in range(4):
                initial = transform_block(block,turn)
                for shift in sorted(contact_shifts(left,initial)):
                    right = transform_block(block,turn,shift)
                    tested += 1
                    valid = legal_contact(left,right)
                    w,e,s,n = COLORS[i]
                    W,E,S,N = COLORS[j]
                    expected = turn == 0 and ((shift == (3,0) and e == W) or
                        (shift == (-3,0) and w == E) or (shift == (0,2) and n == S) or
                        (shift == (0,-2) and s == N))
                    assert valid == expected, (i,j,turn,shift,valid,expected)
                    if valid:
                        contacts.append({'left':i+1,'right':j+1,'turn':turn,'shift':list(shift)})
    return {'forced_pairs':forced,'tested_rectangle_contacts':tested,'legal_rectangle_contacts':contacts,
            'legal_contact_count':len(contacts),'rotated_or_staggered_legal_contacts':0,
            'conclusion':'Each L state has a unique opposite-role partner. Every pair is a 3-by-2 rectangle. Legal rectangle contacts are exactly aligned Jeandel--Rao neighbors with the same orientation.'}


def bump(z):
    import numpy as np
    z = np.asarray(z,dtype=float)
    out = np.zeros_like(z)
    mask = abs(z) < 1
    out[mask] = np.exp(1-1/(1-z[mask]**2))
    return out


def field_values(points, state):
    import numpy as np
    points = np.asarray(points,dtype=float)
    result = np.zeros(len(points))
    for (p,q,normal), amplitude in zip(EDGES,state['amplitudes']):
        tangent = np.array(subtract(q,p))
        local = points-np.array(p)
        s = local@tangent
        r = -local@np.array(normal)
        # Tangential support 1/4<s<3/4; inward collar 0<=r<1/8.
        profile = bump(4*(s-.5))*np.exp(2*state['profile_direction']*(s-.5))
        profile *= bump(r/DELTA)*(r>=-1e-14)
        result += amplitude*profile
    return result


def render(states):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from matplotlib.colors import PowerNorm
    x,y = np.meshgrid(np.linspace(0,2,301),np.linspace(0,2,301))
    points = np.column_stack([x.ravel(),y.ravel()])
    missing = (x>1)&(y>1)
    values = [np.ma.array(field_values(points,state).reshape(x.shape),mask=missing) for state in states]
    peak = max(float(z.max()) for z in values)
    fig,axes = plt.subplots(6,4,figsize=(11,16.5))
    fig.subplots_adjust(left=.035,right=.88,bottom=.025,top=.935,hspace=.46,wspace=.31)
    for ax,state,z in zip(axes.flat,states,values):
        image=ax.imshow(z,origin='lower',extent=(0,2,0,2),cmap='viridis',norm=PowerNorm(.4,vmin=0,vmax=peak))
        ax.add_patch(Polygon(POLYGON,closed=True,fill=False,lw=1.2))
        ax.set_xlim(-.2,2.3);ax.set_ylim(-.2,2.3);ax.set_xticks([]);ax.set_yticks([]);ax.axis('off')
        ax.set_title(r'$%s_{%s}$' % (state['role'],state['wang_id']),fontsize=13,pad=3)
        for (p,q,normal),amplitude in zip(EDGES,state['amplitudes']):
            midpoint=(np.array(p)+q)/2+.12*np.array(normal)
            ax.text(*midpoint,r'$%d$'%amplitude,ha='center',va='center',fontsize=8,
                    color='#4a3941',bbox={'facecolor':'white','edgecolor':'none','pad':.3,'alpha':.8})
    for ax in list(axes.flat)[22:]: ax.axis('off')
    fig.suptitle('Twenty-two field states on the same L-triomino',fontsize=19,y=.98)
    fig.text(.5,.954,'Exact smooth boundary carriers; infinite ordinary Neumann expansions',ha='center',fontsize=11)
    cax=fig.add_axes([.90,.23,.012,.5]);fig.colorbar(image,cax=cax).set_label(r'$u(x,y)$')
    path=ROOT/'l-boundary-palette.png';fig.savefig(path,dpi=140,facecolor='white');plt.close(fig)

    # Draw the forced pair without introducing another physical tile shape.
    fig,ax=plt.subplots(figsize=(9,5.8));ax.set_aspect('equal');ax.axis('off')
    a,b=placement(states[0]),placement(states[1],2,(3,2))
    for polygon,color,label,position in [(POLYGON,'#e7efec',r'$A_1$',(.55,.65)),
        ([add(rotate(p,2),(3,2)) for p in POLYGON],'#f5ecd9',r'$B_1$',(2.45,1.35))]:
        ax.add_patch(Polygon(polygon,facecolor=color,edgecolor='#263b3d',lw=2))
        ax.text(*position,label,fontsize=23,ha='center')
    common=a['edges'].keys()&b['edges'].keys()
    for member in [a,b]:
        for (p,q),(amplitude,direction,normal) in member['edges'].items():
            if (p,q) in common and member is b:continue
            ax.plot([p[0],q[0]],[p[1],q[1]],color='#b46343' if (p,q) in common else '#147b7b',lw=4)
            midpoint=(np.array(p)+q)/2+.16*np.array(normal)
            ax.text(*midpoint,r'$%d$'%amplitude,fontsize=13,ha='center',va='center',
                    bbox={'facecolor':'white','edgecolor':'none','pad':1,'alpha':.8})
    ax.set_xlim(-.5,3.5);ax.set_ylim(-.45,2.45)
    ax.set_title('Boundary matching forces this pair of L-triominoes',fontsize=15,pad=15)
    fig.tight_layout();paired=ROOT/'l-boundary-forced-pair.png';fig.savefig(paired,dpi=160);plt.close(fig)
    return [{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [path,paired]]


def main():
    states=palette()
    evidence=audit(states)
    import numpy as np
    maximum=0.
    for state in states:
        for (p,q,normal),amplitude in zip(EDGES,state['amplitudes']):
            for s in [.0,.19,.375,.5,.61,.82,1.]:
                expected=amplitude*float(bump(4*(s-.5)))*np.exp(2*state['profile_direction']*(s-.5))
                value=float(field_values([add(p,tuple(s*t for t in subtract(q,p)))],state)[0])
                maximum=max(maximum,abs(value-expected))
    assert maximum<1e-12
    output={'date':'2026-10-09','status':'passed','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'geometry':{'cells':sorted(CELLS),'polygon':POLYGON,'unit_boundary_edges':EDGES,'area':3},
        'palette':states,'number_of_field_states':22,'source_color_tuples_W_E_S_N':COLORS,
        'source':'https://arxiv.org/html/1506.06492v4#S4.F4; Figure 4, Theorem 3',
        'allowed_placements':'Integer translations and four quarter-turn rotations; no reflections; fixed amplitudes.',
        'ordinary_boundary_operator':'Homogeneous Neumann Laplacian on the L-triomino.',
        'modal_status':'Each smooth field has an infinite Neumann eigenfunction expansion converging in the H1 form norm. This encoding cannot be a finite eigenfunction sum because its traces vanish on open intervals of a straight side and are nonzero elsewhere on that side.',
        'matching_semantics':'Scalar values agree on every boundary contact. A unit trace is amplitude times the common asymmetric compact profile, forward or reversed. Equality is exactly equality of amplitude and profile direction.',
        'collar_width':DELTA,'maximum_sample_trace_error':maximum,'contact_audit':evidence,
        'infinite_claim':'Exact forced-pair reduction to the cited aperiodic set: every legal infinite L tiling decodes to an aperiodic Wang tiling. Every Wang tiling expands to a legal L tiling. Infinite existence and no translation periods use the source theorem.',
        'limitations':['Boundary conditions alone do not force aperiodicity; the finite allowed field palette is essential.',
            'The palette has finitely many states, but each state uses infinitely many Neumann modes.',
            'The total fields are static and not single-eigenvalue Helmholtz solutions.',
            'No claim of forcing the chair substitution; the hierarchy is inherited from the encoded Wang system.',
            'Reflections and noninteger placements are excluded. No minimality claim.',
            'No GCTS search engine or finite-patch aperiodicity inference.'],
        'figures':render(states)}
    (ROOT/'l-boundary-palette.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'status':'passed','states':22,'forced_pairs':len(evidence['forced_pairs']),
                      'tested_rectangle_contacts':evidence['tested_rectangle_contacts'],
                      'legal_rectangle_contacts':evidence['legal_contact_count'],
                      'maximum_sample_trace_error':maximum},indent=2))


if __name__=='__main__':main()
