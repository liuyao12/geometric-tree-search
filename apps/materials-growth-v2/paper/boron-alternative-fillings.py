"""Independent occurrence choices with frozen learned t; random objective controls.

Not reference search, not uniformly sampled covers, not coordinate-blind growth.
"""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import networkx as nx
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix


def solve(cfg, types, r, seed):
    n = len(cfg['occurrences'])
    rows, cols, vals = [], [], []
    for j,o in enumerate(cfg['occurrences']):
        for u,p in enumerate(o['ids']):
            role = r['roleOfSite'][types[o['type']]['offset']+u]
            rows.append(p); cols.append(j); vals.append(r['weightsByRole'][role])
    lo = [r['capacity']]*cfg['atoms']; hi = lo.copy()
    # Retain the parent training requirement: each observed finite-face type.
    for typ in sorted({o['type'] for o in cfg['occurrences'] if types[o['type']]['kind']=='finite-face'}):
        row = len(lo); lo.append(1); hi.append(np.inf)
        for j,o in enumerate(cfg['occurrences']):
            if o['type']==typ:
                rows.append(row); cols.append(j); vals.append(1)
    costs = np.random.default_rng(seed).uniform(-1,1,n)
    cuts = set(); history = []
    for iteration in range(8):
        a = coo_matrix((vals,(rows,cols)),shape=(len(lo),n)).tocsc()
        fit = milp(costs, integrality=np.ones(n), bounds=Bounds(np.zeros(n),np.ones(n)),
                   constraints=LinearConstraint(a,lo,hi),options={'time_limit':2,'mip_rel_gap':0})
        if fit.x is None:
            return {'seed':seed,'status':'no incumbent; unknown','history':history,'solverStatus':fit.message}
        chosen = np.flatnonzero(fit.x>.5).tolist()
        totals = [0]*cfg['atoms']; graph = nx.Graph(); graph.add_nodes_from(range(cfg['atoms']))
        at = [[] for _ in totals]
        for j in chosen:
            o = cfg['occurrences'][j]
            graph.add_edges_from((o['ids'][0],p) for p in o['ids'][1:])
            for u,p in enumerate(o['ids']):
                role = r['roleOfSite'][types[o['type']]['offset']+u]
                totals[p] += r['weightsByRole'][role]; at[p].append(role)
        assert all(v==r['capacity'] for v in totals)
        parts = list(nx.connected_components(graph))
        history.append({'iteration':iteration,'components':len(parts),'cuts':len(cuts),'solverStatus':fit.message})
        result = {'seed':seed,'status':'exact connected filling' if len(parts)==1 else 'exact disconnected filling; connectivity unresolved',
                  'selected':chosen,'components':len(parts),'history':history,
                  'markDisagreementPoints':sum(len({r['scalarLabelsByRole'][q] for q in group})>1 for group in at)}
        if len(parts)==1:
            return result
        memberships = {p:k for k,part in enumerate(parts) for p in part}
        crossings = [set() for _ in parts]
        for j,o in enumerate(cfg['occurrences']):
            touched = {memberships[p] for p in o['ids']}
            if len(touched)>1:
                for k in touched: crossings[k].add(j)
        for crossing in crossings:
            key = tuple(sorted(crossing))
            if key not in cuts:
                cuts.add(key); row=len(lo); lo.append(1); hi.append(np.inf)
                for j in key: rows.append(row); cols.append(j); vals.append(1)
    return result


if __name__=='__main__':
    inp, learned, dest = map(Path,sys.argv[1:])
    d=json.loads(inp.read_text()); r=json.loads(learned.read_text())['result']
    runs=[]
    for fold,cfg in enumerate(d['configurations']):
        for seed in (101,202):
            out=solve(cfg,d['types'],r,seed)
            out.update(fold=fold,file=cfg['file'])
            runs.append(out)
            print(json.dumps({k:v for k,v in out.items() if k not in ('selected','history')}),flush=True)
    dest.write_text(json.dumps({'inputHash':hashlib.sha256(inp.read_bytes()).hexdigest(),
        'learningHash':hashlib.sha256(learned.read_bytes()).hexdigest(),
        'scope':__doc__,'runs':runs},indent=2)+'\n')
