#!/usr/bin/env python3
"""Numerical Neumann-mode projections of the exact L-only field palette.

Finite truncations are illustrations, never exact matching-rule palettes.
Mass fractions concern the sampled P1 target and are not continuum enclosures.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from compute_modes import seed_polygon, matrices, solve_modes
from l_boundary_palette import palette, field_values, POLYGON

ROOT = Path(__file__).resolve().parent


def main():
    states = palette()
    polygon = np.array(POLYGON[:-1],float)
    seed = seed_polygon(polygon,'pq28a0.012')
    runs = []
    for level in (2,3):
        assembled = matrices(seed,level)
        p,t,boundary,K,M,area = assembled
        values,vectors,diagnostics,free,mass,residuals = solve_modes(assembled,'N',180,polygon,None)
        targets = np.column_stack([field_values(p,state) for state in states])
        coefficients = vectors.T@(M@targets)
        norms = np.sum(targets*(M@targets),axis=0)
        records = []
        for index,state in enumerate(states):
            record = {'id':state['id'],'cosine_only':False,
                      'coefficients_first_180':[float(x) for x in coefficients[:,index]],
                      'truncations':[]}
            for count in (16,32,64,128,180):
                fit = vectors[:,:count]@coefficients[:count,index]
                error = fit-targets[:,index]
                record['truncations'].append({'modes':count,
                    'sampled_target_mass_fraction':float(sum(coefficients[:count,index]**2)/norms[index]),
                    'relative_sampled_mass_error':float(np.sqrt(error@(M@error)/norms[index])),
                    'maximum_sampled_boundary_value_error':float(max(abs(error[boundary]))),
                    'maximum_sampled_boundary_value_error_over_peak':float(max(abs(error[boundary]))/max(abs(targets[:,index])))})
            records.append(record)
        runs.append({'mesh_level':level,'diagnostics':diagnostics,'eigenvalues':values.tolist(),'states':records})
        print(json.dumps({'mesh_level':level,'nodes':len(p),'max_positive_residual':diagnostics['max_positive_relative_residual'],
                          'A1_mass_fraction_180':records[0]['truncations'][-1]['sampled_target_mass_fraction']}),flush=True)
    movement = max(abs(a-b)/max(1,abs(b)) for a,b in zip(runs[0]['eigenvalues'],runs[1]['eigenvalues']))
    assert max(runs[-1]['diagnostics']['max_positive_relative_residual'],
               runs[-1]['diagnostics']['max_mass_orthogonality_error']) < 1e-7
    tr = Triangulation(p[:,0],p[:,1],t)
    fields = []
    for index in (0,1):
        fields.extend([targets[:,index],vectors[:,:64]@coefficients[:64,index],vectors@coefficients[:,index]])
    low,high = min(float(z.min()) for z in fields),max(float(z.max()) for z in fields)
    fig,axes = plt.subplots(2,3,figsize=(10.8,7.8))
    for ax,z,title in zip(axes.flat,fields,[r'$A_1$: sampled exact field',r'$A_1$: first $64$ FEM modes',r'$A_1$: first $180$ FEM modes',
                                          r'$B_1$: sampled exact field',r'$B_1$: first $64$ FEM modes',r'$B_1$: first $180$ FEM modes']):
        image=ax.tripcolor(tr,z,shading='gouraud',cmap='viridis',vmin=low,vmax=high)
        outline=np.array(POLYGON);ax.plot(outline[:,0],outline[:,1],color='#25353a',lw=1)
        ax.set_aspect('equal');ax.set_title(title,fontsize=11);ax.set_xticks([]);ax.set_yticks([])
    fig.subplots_adjust(left=.03,right=.9,bottom=.035,top=.9,wspace=.15,hspace=.2)
    fig.suptitle('Finite mode sums approximate the fields and disturb their matching traces',fontsize=14,y=.97)
    cax=fig.add_axes([.93,.2,.015,.6]);fig.colorbar(image,cax=cax).set_label(r'$u(x,y)$')
    image_path=ROOT/'l-modal-truncations.png';fig.savefig(image_path,dpi=160,facecolor='white');plt.close(fig)
    output={'date':'2026-10-09','status':'passed','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'input_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['l_boundary_palette.py','compute_modes.py','compute.py']},
            'operator':'Ordinary homogeneous Neumann Laplacian on the L-triomino only.',
            'mesh_runs':runs,'maximum_last_refinement_relative_eigenvalue_change':movement,
            'atlas':{'file':image_path.name,'sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),'shared_color_range':[low,high]},
            'limitations':'FEM estimates and projections of sampled P1 targets; no continuum error enclosures. Every truncated palette disturbs exact trace identities and is not proved to tile, much less force aperiodicity. Eigenvectors have natural weak Neumann conditions; their plotted P1 normal derivatives need not vanish pointwise.'}
    (ROOT/'l-modal-projection.json').write_text(json.dumps(output,indent=2)+'\n')


if __name__=='__main__':main()
