"""Capacity-preserving propositional families over the frozen full region graph.

Mine MP fragments from freshly searched proofs, abstract nullary donor atoms,
and join them to actual available formula receptors. A proposal may have gaps
and compound formula bindings. It never changes the base inventory or degrees.
Every constituent runs through global propagation and generation scheduling.
This is a bounded semantic point adapter, not a fixed literal Wang palette.
"""
import collections
import itertools
import math
import random
import time

import movable_proof_regions as M
import quantified_receptors as Q
import check_movable_regions as A
from proof_clusters import digest
from turtle import CAPACITY

FEATURES = ('cells', 'concludes_target', 'progress', 'compactness', 'defer')


def abstract(a, names):
    if a[0] == 'pred' and not a[2]:
        if a[1] not in names:
            names[a[1]] = len(names)
        return ('meta', names[a[1]])
    if a[0] in ('imp', 'and', 'or', 'not'):
        return (a[0],)+tuple(abstract(v, names) for v in a[1:])
    if a == ('bot',):
        return a
    raise ValueError('donor fragment must be propositional over nullary atoms')


def match(pattern, formula, env):
    if pattern[0] == 'meta':
        n = str(pattern[1])
        if n in env:
            return env[n] == formula
        env[n] = formula
        return True
    return (pattern[0] == formula[0] and len(pattern) == len(formula)
            and all(match(p, a, env) for p, a in zip(pattern[1:], formula[1:])))


def promote(spec, catalog, result, library=(), maximum=6):
    if result['status'] != 'finite_exact_proof_region':
        raise ValueError('only a freshly searched complete proof can be mined')
    tiles = [A.tile(catalog['rules'], spec, k) for k in result['placements']]
    checked = A.certificate(catalog['rules'], spec, result, tiles)
    rows = sorted((k for k in result['placements'] if k[1] >= 0), key=lambda k:k[0])
    old = {t['name']:t for t in library}
    known = {digest(t['pattern']) for t in library}
    out = []
    for first in range(len(rows)):
        for size in range(2, min(maximum, len(rows)-first)+1):
            window = rows[first:first+size]
            if any(catalog['rules'][k[1]]['kind'] != 'mp' for k in window):
                continue
            inside = {k[0]:i for i,k in enumerate(window)}
            names, external, pattern = {}, {}, []
            for slot, rid, refs in window:
                rule = catalog['rules'][rid]
                contacts = []
                for ref in refs:
                    if ref in inside:
                        contacts.append(('inside', inside[ref]))
                    else:
                        if ref not in external:
                            external[ref] = len(external)
                        contacts.append(('outside', external[ref]))
                pattern.append(dict(kind='mp', inputs=[abstract(a,names) for a in rule['inputs']],
                                    output=abstract(rule['output'],names), refs=contacts))
            identity = digest(pattern)
            if identity in known:
                continue
            children = []
            for tr in result.get('solution_transactions', ()):
                if tr['item']['template'] in old and set(M.freeze(tr['item']['members'])) <= set(window):
                    children.append(dict(template=tr['item']['template'],
                                         offsets=[inside[k[0]] for k in M.freeze(tr['item']['members'])]))
            level = 1+max((old[ch['template']]['level'] for ch in children), default=0)
            out.append(dict(name='receptor-cluster-'+identity[:20], pattern=pattern, level=level,
                            children=children, source=dict(spec=spec, catalog=catalog, result=result,
                                                           members=window, check=checked)))
            known.add(identity)
    return out


def aggregate(model, members):
    members = M.freeze(members)
    if len(set(members)) != len(members):
        raise ValueError('distinct constituent identities')
    t, marks = collections.Counter(), {}
    for k in members:
        part = model.placement(k)
        for p,v in part.occupancy:
            t[p] += v
            if t[p] > CAPACITY:
                raise ValueError('cluster capacity')
        for p,v in part.marks:
            if p in marks and marks[p] != v:
                raise ValueError('cluster marking disagreement')
            marks[p] = v
    return dict(occupancy=tuple(sorted(t.items())), marks=tuple(sorted(marks.items())))


def proposals(model, state, graph, point, library, limit=12):
    """Finite proposal join. Truncation affects hints only, never base domains.

    External receptors must be hypotheses or actually occupied earlier cells.
    All MP ground rules are eligible; increasing cell embeddings allow gaps.
    The cap is applied after deterministic enumeration, separately from graph
    completeness. No restriction from this join is supplied as a pruning rule.
    """
    available = {i:a for i,a in graph.ports.items()
                 if i < 0 or Q.cell(i) in state.totals}
    slots = [j for j in range(model.bound) if Q.cell(j) in graph.domains]
    pool = {}
    scanned = 0
    for template in sorted(library, key=lambda t:(-len(t['pattern']),t['name'])):
        n = len(template['pattern'])
        for embedding in itertools.combinations(slots,n):
            if point[0]//2 not in embedding:
                continue
            partial = [((),{}, {})]
            for i,node in enumerate(template['pattern']):
                following = []
                j = embedding[i]
                for members,env,outside in partial:
                    for rid,r in enumerate(model.catalog['rules']):
                        if r['kind'] != node['kind']:
                            continue
                        binding = dict(env)
                        if not all(match(p,a,binding) for p,a in zip(node['inputs'],r['inputs'])) or not match(node['output'],r['output'],binding):
                            continue
                        choices = []
                        for (kind,ref),a in zip(node['refs'],r['inputs']):
                            if kind == 'inside':
                                if ref >= i:
                                    raise ValueError('acyclic fragment')
                                choices.append((embedding[ref],))
                            elif str(ref) in outside:
                                v = outside[str(ref)]
                                choices.append((v,) if available.get(v)==a and v<j else ())
                            else:
                                choices.append(tuple(v for v,b in sorted(available.items()) if b==a and v<j))
                        for refs in itertools.product(*choices):
                            key = (j,rid,tuple(refs))
                            if key not in graph.domains[Q.cell(j)]:
                                continue
                            ext = dict(outside)
                            okay = True
                            for (kind,ref),v in zip(node['refs'],refs):
                                if kind == 'outside':
                                    if str(ref) in ext and ext[str(ref)]!=v:
                                        okay=False;break
                                    ext[str(ref)]=v
                            if okay:
                                following.append((members+(key,),binding,ext))
                        scanned += 1
                partial = following
                if not partial:
                    break
            for members,env,outside in partial:
                try:
                    union = aggregate(model,members)
                except ValueError:
                    continue
                if not all(p not in state.marks or state.marks[p]==v for p,v in union['marks']):
                    continue
                item = dict(template=template['name'], members=members, bindings=env,
                            outside=outside, level=template['level'], **union)
                pool.setdefault(members,item)
    result = sorted(pool.values(),key=lambda t:(-int(model.catalog['rules'][t['members'][-1][1]]['output']==model.target),
                                               -len(t['members']),digest(t)))
    return result[:limit],dict(compatible=len(result),scanned=scanned,truncated=max(0,len(result)-limit))


class Budget(Exception):
    pass


def execute(model, state, graph, item, tick=None):
    before = graph.fingerprint()
    snapshot = state.copy()
    child,cg = state.copy(),graph.copy()
    members = M.freeze(item['members'])
    if M.freeze(aggregate(model,members)) != M.freeze({k:item[k] for k in ('occupancy','marks')}):
        raise ValueError('actual aggregate must equal every original constituent')
    pending,steps = set(members),[]
    status = 'accepted_cluster'
    while pending:
        kind,p,keys = cg.decision(child)
        if kind in ('dead','empty'):
            status='rejected_'+kind;break
        if kind == 'forced':
            key=keys[0]
        else:
            eligible=sorted(k for k in pending if k in keys)
            if not eligible:
                status='rejected_scheduler';break
            key=eligible[0]
        if tick:
            try:tick()
            except Budget:status='unknown_transaction_budget';break
        role='member' if key in pending else 'global_forced'
        cg.update(model,child,child.place(model.placement(key)))
        pending.discard(key)
        steps.append(dict(kind=kind,point=p,key=key,role=role))
    if status == 'accepted_cluster' and cg.decision(child)[0]=='dead':
        status='rejected_dead'
    if state != snapshot or graph.fingerprint()!=before:
        raise ValueError('exact caller rollback')
    trace=dict(status=status,steps=steps)
    return (trace,child,cg) if status=='accepted_cluster' else (trace,None,None)


def features(item, model, state):
    if item is None:
        return (0,0,0,0,1)
    slots=[k[0] for k in item['members']]
    return (len(slots)/6,int(model.catalog['rules'][item['members'][-1][1]]['output']==model.target),
            len(state.order)/model.length,len(slots)/(max(slots)-min(slots)+1),0)


def choose(items, model, state, weights, stochastic, rng):
    fs=[features(None,model,state)]+[features(t,model,state) for t in items]
    scores=[sum(w*v for w,v in zip(weights,f)) for f in fs]
    scale=max(scores)
    masses=[math.exp(v-scale) for v in scores]
    probabilities=[v/sum(masses) for v in masses]
    draw=rng.random() if stochastic else None
    selected=max(range(len(scores)),key=lambda i:(scores[i],-i))
    if stochastic:
        acc=0
        for i,p in enumerate(probabilities):
            acc+=p
            if draw<acc:selected=i;break
    gradient=[fs[selected][j]-sum(p*f[j] for p,f in zip(probabilities,fs)) for j in range(len(FEATURES))]
    event=dict(features=fs,probabilities=probabilities,draw=draw,selected=selected,gradient=gradient)
    return (None if selected==0 else items[selected-1]),event


def update(weights, baseline, result, rate=.15):
    m=result['metrics']
    reward=int(result['status']=='finite_exact_proof_region')-math.log1p(m.get('attempts',0))/math.log1p(result['limits']['attempts'])
    gradients=[e['gradient'] for e in result['policy_events']]
    gradient=[sum(g[j] for g in gradients)/max(1,len(gradients)) for j in range(len(FEATURES))]
    next_weights=[max(-6,min(6,w+rate*(reward-baseline)*g)) for w,g in zip(weights,gradient)]
    return next_weights,.9*baseline+.1*reward,dict(reward=reward,baseline_before=baseline,
                                                gradient=gradient,rate=rate,weights_after=next_weights)


def search(model, library=(), mode='base', weights=None, stochastic=False, seed=0,
           attempts=5000, seconds=5, proposal_limit=12):
    if mode not in ('base','fixed','policy'):
        raise ValueError('declared proposal control')
    if mode=='policy' and (weights is None or len(weights)!=len(FEATURES)):
        raise ValueError('frozen episode weights')
    began=time.perf_counter()
    state=model.initial();graph=M.Graph(model,state)
    metrics=collections.Counter();events=[];found=None;best=state;transactions=[]
    rng=random.Random(seed)
    def tick():
        if metrics['attempts']>=attempts or time.perf_counter()-began>seconds:
            raise Budget()
        metrics['attempts']+=1
    def visit(s,g,path):
        nonlocal found,best,transactions
        metrics['nodes']+=1
        kind,p,keys=g.decision(s)
        tree=dict(kind=kind,point=p,proposals=[],children=[])
        metrics['peak_candidates']=max(metrics['peak_candidates'],sum(len(d) for d in g.domains.values()))
        if time.perf_counter()-began>seconds:
            tree['cutoff']='entry_wall';return None,tree
        if len(s.order)>len(best.order) and kind!='dead':best=s
        if kind=='dead':metrics['dead']+=1;return False,tree
        if kind=='empty':found=s;transactions=path;return True,tree
        metrics[kind]+=1
        if kind=='branch' and mode!='base' and library:
            start=time.perf_counter();items,work=proposals(model,s,g,p,library,proposal_limit)
            metrics['proposal_seconds']+=time.perf_counter()-start
            for k,v in work.items():metrics['proposal_'+k]+=v
            item=items[0] if items else None
            if mode=='policy':
                item,event=choose(items,model,s,weights,stochastic,rng)
                event.update(id=len(events),chosen=tuple(s.order),point=p,
                             items=items)
                tree['policy_event']=len(events);events.append(event)
            if item is not None:
                metrics['proposal_trials']+=1
                start=time.perf_counter();trace,child,cg=execute(model,s,g,item,tick)
                metrics['transaction_seconds']+=time.perf_counter()-start
                metrics['constituent_steps']+=len(trace['steps'])
                metrics['constituent_forced']+=sum(t['kind']=='forced' for t in trace['steps'])
                metrics['constituent_branches']+=sum(t['kind']=='branch' for t in trace['steps'])
                trial=dict(item=item,trace=trace);tree['proposals'].append(trial)
                if trace['status']=='unknown_transaction_budget':return None,tree
                if child is not None:
                    metrics['accepted_transactions']+=1
                    okay,sub=visit(child,cg,path+[trial]);trial['tree']=sub
                    if okay is not False:return okay,tree
                    metrics['backtracks']+=1
                else:metrics['rejected_transactions']+=1
        for key in keys:
            try:tick()
            except Budget:tree['cutoff']='base_before_placement';return None,tree
            metrics['singleton_attempts']+=1
            child,cg=s.copy(),g.copy();cg.update(model,child,child.place(model.placement(key)))
            okay,sub=visit(child,cg,path);tree['children'].append(dict(key=key,tree=sub))
            if okay is not False:return okay,tree
            metrics['backtracks']+=1
        return False,tree
    okay,tree=visit(state,graph,[])
    selected=found or best
    rows,endpoint=M.decode(model,selected.order) if found else (None,None)
    return dict(status='finite_exact_proof_region' if okay else 'unknown_search_budget' if okay is None else 'exhausted_finite_region',
                placements=selected.order,tile_generations=selected.tile_generations,proof=rows,endpoint=endpoint,
                metrics=dict(metrics),seconds=time.perf_counter()-began,candidate_universe=model.cardinality(),
                solution_transactions=transactions,policy_events=events,weights=weights,stochastic=stochastic,
                seed=seed,mode=mode,search_tree=tree,limits=dict(attempts=attempts,seconds=seconds,proposal_limit=proposal_limit))
