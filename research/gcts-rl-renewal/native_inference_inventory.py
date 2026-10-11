"""Mine typed dependency fragments; bind their shapes to current receptors.

Templates contain only rule/port topology, never donor formula words, names,
slot coordinates or a target proof. Each binding expands to original command
and guard placements. Additional sampled clusters keep proposal types open.
All proposals are ordering hints, never a candidate-domain restriction.
"""
import collections,hashlib,itertools
from certificate_boundary_search import canonical,digest

def mine(model,placements,donor):
    guards={k[0]:k for k in placements if k[1]==1};rows=[]
    for count in range(1,min(3,len(guards))+1):
        for slots in itertools.combinations(sorted(guards),count):
            index={j:i for i,j in enumerate(slots)};edges={i:set() for i in range(count)};holes={};nodes=[]
            for j in slots:
                meta=model.metadata[guards[j]];inputs=[]
                for source,_ in meta['requirements']:
                    if source in index:
                        inputs.append(dict(node=index[source]));edges[index[j]].add(index[source]);edges[index[source]].add(index[j])
                    else:inputs.append(dict(hole=holes.setdefault(source,len(holes))))
                nodes.append(dict(rule=meta['command']['rule'],inputs=inputs))
            reached={0};pending=[0]
            while pending:
                for nxt in edges[pending.pop()]-reached:reached.add(nxt);pending.append(nxt)
            if len(reached)!=count:continue
            template=dict(nodes=nodes,holes=len(holes));rows.append(dict(id=digest(template),template=template,level=max(sum(n['rule'] in ('mp','generalize') for n in nodes),1),donors=[dict(case=donor,slots=slots,placements=[x for j in slots for x in ((j,0,guards[j][2],0),guards[j])])]))
    return rows

def combine(rows):
    result={}
    for row in rows:
        key=row['id']
        if key not in result:result[key]=row
        else:result[key]['donors'].extend(row['donors'])
    return sorted(result.values(),key=lambda r:(-len(r['template']['nodes']),r['id']))

def aggregate(model,members,state,record=True):
    """Exact union of distinct constituents, accounting for already used tiles."""
    unique=sorted(set(members));totals={};marks={};fresh=[];new_marks=0
    for key in unique:
        if key not in model.cache:return None
        c=model.cache[key]
        if key in state.selected:continue
        fresh.append(key)
        for p,v in c.occupancy:
            if p not in state.allowed_points or state.totals.get(p,0)+totals.get(p,0)+v>12:return None
            totals[p]=totals.get(p,0)+v
        for p,v in c.marks:
            if p in marks and marks[p]!=v or p in state.marks and state.marks[p]!=v:return None
            if p not in marks and p not in state.marks:new_marks+=1
            marks[p]=v
    if not record:return True
    return dict(members=unique,pending=fresh,aggregate_sha256=digest(dict(totals=sorted(totals.items()),marks=sorted(marks.items()))),new_occupancy=sum(totals.values()),new_marks=new_marks)

class Join:
    def __init__(self,model,library):
        self.model=model;self.library=library;self.by_rule=collections.defaultdict(list)
        for key,meta in sorted(model.metadata.items()):
            if key[1]==1:self.by_rule[meta['command']['rule']].append(key)
    def __call__(self,state,graph,point,limit=24,checks=2048):
        model=self.model;pool=[];seen=set();work=collections.Counter();stopped=False;family_stopped=False;family_end=limit;family_check_end=checks;anchors=sorted(graph.domains[point])
        def valid_members(members,record=False):
            nonlocal stopped,family_stopped
            if work['validation_checks']>=checks:stopped=True;return None
            if work['validation_checks']>=family_check_end:family_stopped=True;return None
            work['validation_checks']+=1;return aggregate(model,members,state,record=record)
        def save(kind,members,**extra):
            record=valid_members(members,record=True)
            if record is None:return
            ident=tuple(record['members'])
            if ident in seen:return
            if not any(k in graph.domains[point] for k in record['pending']):return
            seen.add(ident);record.update(kind=kind,**extra);record['id']=digest(dict(kind=kind,members=record['members'],family=extra.get('family')));pool.append(record)
        def instance(family,anchor_node,anchor_guard):
            template=family['template'];nodes=template['nodes'];assigned={};holes={};members=[]
            order=[anchor_node]+[i for i in range(len(nodes)) if i!=anchor_node]
            def bind(depth):
                if stopped or family_stopped or len(pool)>=family_end:return
                if depth==len(order):
                    save('family',members,family=family['id'],bindings=dict(nodes=sorted(assigned.items()),holes=sorted(holes.items())),level=family['level']);return
                node=order[depth];descriptor=nodes[node];required_slots=[];required_formulas=[]
                for other,key in assigned.items():
                    meta=model.metadata[key]
                    for input_id,port in enumerate(nodes[other]['inputs']):
                        if port.get('node')==node:required_slots.append(meta['requirements'][input_id][0]);required_formulas.append(meta['requirements'][input_id][1])
                if required_slots and len(set(required_slots))!=1:return
                candidates=[anchor_guard] if depth==0 else self.by_rule[descriptor['rule']]
                for guard in candidates:
                    if stopped or family_stopped or len(pool)>=family_end:return
                    meta=model.metadata[guard];slot=guard[0]
                    if required_slots and slot!=required_slots[0]:continue
                    if any(f!=meta['command']['formula'] for f in required_formulas):continue
                    if slot in [k[0] for k in assigned.values()] or slot in holes.values():continue
                    if len(meta['requirements'])!=len(descriptor['inputs']):continue
                    if any('node' in port and port['node'] in assigned and (meta['requirements'][r][0]!=assigned[port['node']][0] or meta['requirements'][r][1]!=model.metadata[assigned[port['node']]]['command']['formula']) for r,port in enumerate(descriptor['inputs'])):continue
                    new_holes=holes.copy();okay=True
                    for r,port in enumerate(descriptor['inputs']):
                        if 'hole' in port:
                            source=meta['requirements'][r][0];hid=port['hole']
                            if hid in new_holes and new_holes[hid]!=source:okay=False;break
                            if source==slot or source in [k[0] for k in assigned.values()] or any(h!=hid and s==source for h,s in new_holes.items()):okay=False;break
                            new_holes[hid]=source
                    if not okay:continue
                    pair=[(slot,0,guard[2],0),guard];trial=valid_members(members+pair)
                    if trial is None:continue
                    prior=holes.copy();holes.clear();holes.update(new_holes);assigned[node]=guard;members.extend(pair)
                    bind(depth+1)
                    del members[-2:];del assigned[node];holes.clear();holes.update(prior)
            bind(0)
        # Balance the bounded pool across selected-point candidates first,
        # then across template families. A failed early binding cannot consume
        # another anchor's whole proposal allowance.
        for anchor in anchors[:limit]:
            anchor_end=min(limit,len(pool)+max(1,limit//max(1,min(len(anchors),limit))))
            anchor_checks=min(checks,work['validation_checks']+max(1,checks//max(1,min(len(anchors),limit))))
            for family in self.library:
                family_stopped=False;family_end=min(anchor_end,len(pool)+1);family_check_end=min(anchor_checks,work['validation_checks']+max(1,(checks//max(1,min(len(anchors),limit)))//max(1,len(self.library))))
                for guard in self.by_rule.values():
                    for gkey in guard:
                        if gkey[0]!=anchor[0] or gkey[2]!=anchor[2] or anchor[1]==1 and gkey!=anchor:continue
                        for n,descriptor in enumerate(family['template']['nodes']):
                            if descriptor['rule']==model.metadata[gkey]['command']['rule']:instance(family,n,gkey)
                            if stopped or family_stopped or len(pool)>=family_end:break
                        if stopped or family_stopped or len(pool)>=family_end:break
                    if stopped or family_stopped or len(pool)>=family_end:break
                work['family_budget_stops']+=int(family_stopped);work['family_quota_stops']+=int(len(pool)>=family_end)
                if stopped or len(pool)>=anchor_end or work['validation_checks']>=anchor_checks:break
            if stopped or len(pool)>=limit:break
        work['family_pool']=len(pool);work['family_truncated']=int(stopped or work['family_budget_stops'] or work['family_quota_stops'] or len(pool)>=limit)
        # Eight deterministic sampled clusters from all legal base candidates,
        # unrestricted by the mined rule/port families. This separate proposal
        # allowance cannot change any graph degree or completeness claim.
        all_keys=sorted(graph.edges);sample_checks=0
        for anchor in anchors[:4]:
            ordering=sorted(all_keys,key=lambda k:hashlib.sha256(canonical(dict(anchor=anchor,key=k,chosen=state.order))).digest())
            for count in (1,3):
                chosen=[anchor]
                if count>1:
                    for key in ordering:
                        if sample_checks>=64:break
                        if key in chosen:continue
                        sample_checks+=1
                        if aggregate(model,chosen+[key],state,record=False) is not None:chosen.append(key)
                        if len(chosen)>=count:break
                # Sampling has its own bounded allowance after family checks.
                record=aggregate(model,chosen,state);work['sample_validation_checks']+=1
                if record is not None and tuple(record['members']) not in seen:
                    seen.add(tuple(record['members']));record.update(kind='sampled',family=None,bindings=None,level=0);record['id']=digest(dict(kind='sampled',members=record['members'],family=None));pool.append(record)
            if len(pool)-work['family_pool']>=8:break
        work['sample_pair_tests']=sample_checks;work['items']=len(pool)
        return [None]+pool,dict(work)
