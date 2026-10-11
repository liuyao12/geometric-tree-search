#!/usr/bin/env python3
"""Two-mesh Neumann FEM projections of the sphinx boundary-field palette.

These finite truncations are illustrations, not exact matching palettes.
Errors concern the nodal P1 target and have no continuum enclosures.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from compute_modes import seed_polygon, matrices, solve_modes, pixel_sampler, write_paged_atlas
from sphinx_boundary_palette import palette, field_values, POLYGON

ROOT = Path(__file__).resolve().parent


def main():
    states=palette(); polygon=np.array(POLYGON,float)
    seed=seed_polygon(polygon,'pq28a0.012'); runs=[]
    for level in (2,3):
        assembled=matrices(seed,level)
        p,t,boundary,K,M,area=assembled
        values,vectors,diagnostics,free,mass,residuals=solve_modes(assembled,'N',180,polygon,None)
        targets=np.column_stack([field_values(p,state) for state in states])
        coefficients=vectors.T@(M@targets)
        norms=np.sum(targets*(M@targets),axis=0); records=[]
        assert np.all(np.isfinite(values)) and np.all(np.isfinite(vectors))
        assert np.all(np.isfinite(coefficients)) and np.all(norms>0)
        for index,state in enumerate(states):
            record={'id':state['id'],'sampled_target_squared_mass_norm':float(norms[index]),
                    'coefficients_first_180':coefficients[:,index].tolist(),'truncations':[]}
            for count in (16,32,64,128,180):
                fit=vectors[:,:count]@coefficients[:count,index]; error=fit-targets[:,index]
                assert np.all(np.isfinite(fit))
                record['truncations'].append({'modes':count,
                    'sampled_target_mass_fraction':float(sum(coefficients[:count,index]**2)/norms[index]),
                    'relative_sampled_mass_error':float(np.sqrt(error@(M@error)/norms[index])),
                    'maximum_sampled_boundary_value_error':float(max(abs(error[boundary]))),
                    'maximum_sampled_boundary_value_error_over_peak':float(max(abs(error[boundary]))/max(abs(targets[:,index])))})
            records.append(record)
        runs.append({'mesh_level':level,'diagnostics':diagnostics,'eigenvalues':values.tolist(),'states':records})
        print(json.dumps({'mesh_level':level,'nodes':len(p),'max_positive_residual':diagnostics['max_positive_relative_residual'],
                          'A1_mass_fraction_180':records[0]['truncations'][-1]['sampled_target_mass_fraction']}),flush=True)
    movement=max(abs(a-b)/max(1,abs(b)) for a,b in zip(runs[0]['eigenvalues'],runs[1]['eigenvalues']))
    assert max(runs[-1]['diagnostics']['max_positive_relative_residual'],runs[-1]['diagnostics']['max_mass_orthogonality_error'])<1e-7
    eigen_atlas,peaks=write_paged_atlas('sphinx-boundary-N',vectors,pixel_sampler(p,t,polygon))
    mode_records=[{'index':j,'rank':j+1,'mode':j,'value':float(value),
        'previous_value':runs[0]['eigenvalues'][j],
        'last_change':float(abs(value-runs[0]['eigenvalues'][j])),
        'relative_residual':float(residuals[j]),'mass_normalized_peak':float(peaks[j]),
        'exact_family':None} for j,value in enumerate(values)]
    tr=Triangulation(p[:,0],p[:,1],t); fields=[]
    for index in (0,1):
        fields.extend([targets[:,index],vectors[:,:64]@coefficients[:64,index],vectors@coefficients[:,index]])
    low,high=min(float(z.min()) for z in fields),max(float(z.max()) for z in fields)
    fig,axes=plt.subplots(2,3,figsize=(12,6.8))
    titles=[r'$A_1$: sampled exact field',r'$A_1$: first $64$ FEM modes',r'$A_1$: first $180$ FEM modes',
            r'$B_1$: sampled exact field',r'$B_1$: first $64$ FEM modes',r'$B_1$: first $180$ FEM modes']
    for ax,z,title in zip(axes.flat,fields,titles):
        image=ax.tripcolor(tr,z,shading='gouraud',cmap='viridis',vmin=low,vmax=high)
        outline=np.array(POLYGON+[POLYGON[0]]);ax.plot(outline[:,0],outline[:,1],color='#25353a',lw=1)
        ax.set_aspect('equal');ax.set_title(title,fontsize=11);ax.set_xticks([]);ax.set_yticks([])
    fig.subplots_adjust(left=.03,right=.9,bottom=.03,top=.88,wspace=.18,hspace=.25)
    fig.suptitle('Sphinx fields: finite modal truncations disturb the exact matching traces',fontsize=14,y=.965)
    cax=fig.add_axes([.93,.2,.012,.6]);fig.colorbar(image,cax=cax).set_label(r'$u(x,y)$')
    image_path=ROOT/'sphinx-modal-truncations.png';fig.savefig(image_path,dpi=160,facecolor='white');plt.close(fig)
    output={'date':'2026-10-11','status':'passed','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['sphinx_boundary_palette.py','compute_modes.py','compute.py']},
        'operator':'Ordinary homogeneous Neumann Laplacian on the exact sphinx polygon.',
        'mesh_runs':runs,'maximum_last_refinement_relative_eigenvalue_change':movement,
        'eigenfunction_viewer':{'domains':[{'id':'sphinx','label':'Sphinx','polygon':polygon.tolist(),'area':area,
            'spectra':[{'bc':'N','label':'Neumann','boundary_edges':['N']*5,'checks':diagnostics,
                         'atlas':eigen_atlas,'modes':mode_records}]}]},
        'versions':{'numpy':np.__version__},
        'atlas':{'file':image_path.name,'sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),'shared_color_range':[low,high]},
        'limitations':'Uncertified FEM projections of sampled P1 targets. Finite projections disturb the trace identities; no tiling or aperiodicity claim survives by approximation alone. Neumann conditions are imposed weakly, not as pointwise zero derivatives of the P1 plots.'}
    (ROOT/'sphinx-modal-projection.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
