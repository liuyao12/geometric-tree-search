"""Bounded exact row clusters and open sampled clusters for the factored model."""
import collections,hashlib
from certificate_boundary_search import canonical
from native_inference_inventory import aggregate

FEATURES=('lemma','base_growth','new_fact','justified_inputs','target_output','mark_extension','shape_density','completed_rows','semantic_level','defer')
FIXED=(.7,.3,1.,.8,.2,-.1,.2,.2,.4,0.)

def row_requirements(model,keys,j):
    by_role={k[1]:k for k in keys if k[0]==j}
    if 0 not in by_role or 1 not in by_role:return None
    c=model.metadata[by_role[0]];g=model.metadata[by_role[1]]
    if c['command']!=g['command']:return None
    if any(r not in by_role for r in range(2,2+model.arity)):return None
    if g['command']['rule']!='block':return g['requirements']
    mode=model.mode[g['command']['name']]
    d=next(d for d in model.interfaces if d['name']==g['command']['name'])
    refs=[]
    for r in range(model.arity):
        m=model.metadata[by_role[2+r]]
        if m['mode']!=mode:return None
        if r<len(d['definition']['premises']):
            if m['source'] is None:return None
            refs.append((m['source'],d['definition']['premises'][r]))
        elif m['source'] is not None:return None
    return refs

def known_rows(model,state):
    known=set();facts=set()
    for j in range(model.spec['length']):
        req=row_requirements(model,state.selected,j)
        if req is not None and all(i in known for i,a in req):
            known.add(j);k=next(k for k in state.selected if k[0]==j and k[1]==1)
            facts.add(canonical(model.metadata[k]['command']['formula']))
    return known,facts

def vector(item,model,state,graph):
    if item is None:return [0.]*9+[1.]
    known,facts=known_rows(model,state);slots={k[0] for k in item['members']}
    gs=[model.metadata[k] for k in item['members'] if k[1]==1]
    requirements=[pair for j in slots for pair in (row_requirements(model,list(state.selected)+item['members'],j) or [])]
    # For a partial random cluster, include actual written input requirements
    # rather than granting it a completed logical row.
    if not requirements:requirements=[pair for k in item['members'] for pair in model.metadata[k]['requirements']]
    refs=[i for i,a in requirements]
    full=sum(row_requirements(model,item['members'],j) is not None for j in slots)
    return [float(item['kind']=='lemma'),item['new_occupancy']/(12*(2+model.arity)),
            float(any(canonical(g['command']['formula']) not in facts for g in gs)),
            sum(i in known for i in refs)/max(1,len(refs)),
            float(any(g['command']['formula']==model.spec['target'] for g in gs)),
            item['new_marks']/1000,len(slots)/(max(slots)-min(slots)+1),
            full/max(1,len(slots)),item['level']/2,0.]

class Join:
    def __init__(self,model,enable_lemmas=True):
        self.model=model;self.enable_lemmas=enable_lemmas
        self.guards={j:[] for j in range(model.spec['length'])}
        for k in sorted(model.metadata):
            if k[1]==1:self.guards[k[0]].append(k)
    def __call__(self,state,graph,point,limit=24,checks=2048):
        model=self.model;pool=[];seen=set();work=collections.Counter()
        anchors=sorted(graph.domains[point]);selected_by_point={c.occupancy[0][0]:k for k in state.selected for c in [model.placement(k)]}
        def save(kind,members,level):
            if kind=='sampled':
                work['sample_validation_checks']+=1
            else:
                if work['validation_checks']>=checks:return
                work['validation_checks']+=1
            item=aggregate(model,members,state)
            if item is None:return
            key=tuple(item['members'])
            if key in seen or not any(k in graph.domains[point] for k in item['pending']):return
            seen.add(key);item.update(kind=kind,level=level);pool.append(item)
        for anchor in anchors[:limit]:
            end=min(limit,len(pool)+max(1,limit//max(1,min(limit,len(anchors)))))
            check_end=min(checks,work['validation_checks']+max(1,checks//max(1,min(limit,len(anchors)))))
            j=anchor[0]
            for guard in self.guards[j]:
                if len(pool)>=end or work['validation_checks']>=check_end:break
                command=model.metadata[guard]['command'];block=command['rule']=='block'
                if block and not self.enable_lemmas:continue
                mode=model.mode[command['name']] if block else 0
                pair=[(j,0,guard[2],0),guard]
                if anchor[1]<2 and anchor not in pair:continue
                if any(k not in state.selected and not state.legal(model.placement(k)) for k in pair):continue
                level=next(d['level'] for d in model.interfaces if d['name']==command['name']) if block else 0
                lists=[]
                for role in range(2,2+model.arity):
                    p=(4*j,role)
                    candidates=[selected_by_point[p]] if p in selected_by_point else list(model.align_cache[p])
                    candidates=[k for k in candidates if model.metadata[k]['mode']==mode and (k in state.selected or state.legal(model.placement(k)))]
                    if anchor[1]==role:candidates=[k for k in candidates if k==anchor]
                    lists.append(candidates)
                def extend(r,members):
                    if len(pool)>=end or work['validation_checks']>=check_end:return
                    if r==len(lists):
                        save('lemma' if block else 'primitive',members,level);return
                    for k in lists[r]:
                        if len(pool)>=end or work['validation_checks']>=check_end:return
                        work['validation_checks']+=1
                        if aggregate(model,members+[k],state,record=False):extend(r+1,members+[k])
                extend(0,pair)
            if len(pool)>=end:work['row_quota_stops']+=1
            if work['validation_checks']>=check_end:work['row_check_stops']+=1
        work['row_pool']=len(pool);work['anchors_omitted']=max(0,len(anchors)-limit)
        # Arbitrary clusters from the complete legal original inventory remain
        # eligible, independent of the known semantic row generators.
        legal_keys=sorted({k for ks in graph.domains.values() for k in ks})
        for anchor in anchors[:4]:
            ranked=sorted(legal_keys,key=lambda k:(hashlib.sha256(canonical([anchor,k])).digest(),k))
            save('sampled',[anchor],0)
            members=[anchor]
            for k in ranked:
                if k in members:continue
                if work['sample_pair_tests']>=64:break
                work['sample_pair_tests']+=1
                if aggregate(model,members+[k],state,record=False):members.append(k)
                if len(members)==3:break
            if len(members)>1:save('sampled',members,0)
        work['items']=len(pool)
        return [None]+pool,dict(work)
