"""Finite source-relation adapter and translation-only point compiler, inactive elsewhere.

A row block is a declared symbolic inference tile, not the aggregate t of its
internal primitive proof. Native/compiler/aggregate correspondence is open.
"""
import copy,hashlib,itertools,json
class Invalid(ValueError):pass
def require(ok,msg):
    if not ok:raise Invalid(msg)
def word(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(x):return hashlib.sha256(word(x)).hexdigest()
def f(n):return ['fun',n,[]]
def incident(p,l):return ['pred','Incident',[f(p),f(l)]]
def guard(a,b,u,v):
    parts=[['pred','Point',[f(a)]],['pred','Point',[f(b)]],['pred','Line',[f(u)]],['pred','Line',[f(v)]],['not',['eq',f(a),f(b)]],incident(a,u),incident(b,u),incident(a,v),incident(b,v)]
    out=parts[-1]
    for x in reversed(parts[:-1]):out=['and',x,out]
    return out

def authority(plan):
    return dict(kind='certified_transport',scope='exact_finite_six_rule_symbolic_relation_only',certificate_sha256=plan['inputs'][plan['certificate']]['sha256'],structural_audit_sha256=plan['inputs'][plan['structural_audit']]['sha256'],source_native_record_sha256=plan['inputs'][plan['source_record']]['sha256'],argument_sha256=plan['inputs'][plan['argument']]['sha256'],ledger_sha256=plan['inputs'][plan['ledger']]['sha256'],argument_review_sha256=plan['inputs'][plan['argument_review']]['sha256'],source_request_sha256=plan['source_request_sha256'],epoch=plan['authority_epoch'],native_accepted=False,existing_engine_activated=False)
def registry(cert,auth):
    out=[];prior={}
    for i,r in enumerate(cert['records']):
        d=r['definition'];require(d['name'] not in prior,'distinct declaration identities')
        for n in r['dependencies']:require(n in prior,'complete earlier dependency')
        for row in d['proof']:
            if row['rule']=='block':require(row['name'] in prior and row['name'] in r['dependencies'],'earlier full-body block alias')
        out.append(dict(name=d['name'],family=r['family'],premises=copy.deepcopy(d['premises']),conclusion=copy.deepcopy(d['conclusion']),dependencies=copy.deepcopy(r['dependencies']),definition_sha256=digest(d),source_record_index=i,authority=copy.deepcopy(auth)))
        prior[d['name']]=d
    require(len(out)==171,'full171 interface registry');return out

def compile_rows(rules,seeds,rows,target=None):
    """All relative reference tuples; conflicting local functions are explicit."""
    require(type(rows) is int and rows>=1,'finite row boundary')
    table={word(x):x for r in rules for x in r['premises']+[r['conclusion']]}
    for x in seeds:table[word(x['formula'])]=x['formula']
    if target is not None:table[word(target)]=target
    formulas=[table[k] for k in sorted(table)];code={word(f):i for i,f in enumerate(formulas)}
    descriptors=[dict(name=s['name'],kind=s['kind'],family='seed',premises=[],conclusion=s['formula'],dependencies=[],authority=s.get('authority')) for s in seeds]+[dict(name=r['name'],kind='block',family=r['family'],premises=r['premises'],conclusion=r['conclusion'],dependencies=r['dependencies'],authority=r.get('authority')) for r in rules]
    prototypes=[];rejected=[];key_to_proto={}
    for d in descriptors:
        p=[code[word(x)] for x in d['premises']];o=code[word(d['conclusion'])]
        for offsets in itertools.product(range(1-rows,0),repeat=len(p)):
            marks={(1,0):o};conflict=False
            for k,(delta,value) in enumerate(zip(offsets,p)):
                loc=(1,delta)
                if loc in marks and marks[loc]!=value:conflict=True
                marks[loc]=value;marks[(2+k,0)]=delta
            body=dict(interface=d['name'],kind=d['kind'],family=d['family'],premise_codes=p,conclusion_code=o,input_offsets=list(offsets),dependencies=d['dependencies'],authority=d['authority'],t=[[0,0,1]],m=[[x,y,v] for (x,y),v in sorted(marks.items())])
            key=(d['name'],offsets)
            if conflict:rejected.append(dict(interface=d['name'],input_offsets=list(offsets),reason='inconsistent_local_mark_function'));key_to_proto[key]=None
            else:
                body['id']='prototype-'+digest(body);prototypes.append(body);key_to_proto[key]=body['id']
    placements=[]
    for p in prototypes:
        for row in range(rows):
            placements.append(dict(id=p['id']+'@'+str(row),prototype=p['id'],interface=p['interface'],family=p['family'],kind=p['kind'],row=row,inputs=[row+d for d in p['input_offsets']],premise_codes=p['premise_codes'],conclusion_code=p['conclusion_code'],t=[[0,row,1]],m=[[x,y+row,v] for x,y,v in p['m']]))
    syntax=[]
    for row in range(rows):
        for d in descriptors:
            for refs in itertools.product(range(row),repeat=len(d['premises'])):
                offsets=tuple(j-row for j in refs);pid=key_to_proto[(d['name'],offsets)]
                syntax.append(dict(row=row,interface=d['name'],inputs=list(refs),placement=pid+'@'+str(row) if pid else None,reason='inconsistent_local_mark_function' if pid is None else None))
    fixed=[ [1,y,-1] for y in range(1-rows,0)]
    if target is not None:fixed.append([1,rows-1,code[word(target)]])
    model=dict(version='finite-symbolic-row-point-catalog-1',orientations=['identity'],translations_only=True,formula_codes=formulas,rows=rows,required=[[0,i] for i in range(rows)],root_generations=[[0,i,0] for i in range(rows)],fixed_m=fixed,prototypes=prototypes,rejected_prototypes=rejected,placements=placements,ordered_bindings=syntax,descriptors=descriptors,scope='Declared finite symbolic row grammar; neither full first-order grammar nor aggregate cluster expansion.')
    return model

def compatible(candidate,totals,marks,selected):
    if candidate['id'] in selected:return 'selected'
    if any(totals.get((x,y),0)+v>1 for x,y,v in candidate['t']):return 't_capacity'
    if any((x,y) in marks and marks[(x,y)]!=v for x,y,v in candidate['m']):return 'm_disagreement'
    return None
class Graph:
    """Complete bidirectional t/m bookkeeping; exact transactional rollback."""
    def __init__(self,model):
        self.model=model;self.byid={p['id']:p for p in model['placements']};require(len(self.byid)==len(model['placements']),'distinct placement identities')
        self.required={tuple(q) for q in model['required']};self.generations={tuple(q[:2]):q[2] for q in model['root_generations']};self.totals={q:0 for q in self.required};self.marks={tuple(q[:2]):q[2] for q in model['fixed_m']};self.mark_counts={q:1 for q in self.marks};self.selected=set();self.placement_generations={};self.dependencies={};self.incident={q:set() for q in self.required};self.reverse={}
        for p in model['placements']:
            supports={tuple(q[:2]) for q in p['t']+p['m']};self.reverse[p['id']]=supports
            for q in supports:self.dependencies.setdefault(q,set()).add(p['id'])
            for x,y,v in p['t']:
                if v>0 and (x,y) in self.incident:self.incident[(x,y)].add(p['id'])
        self.valid={k:compatible(p,self.totals,self.marks,self.selected) for k,p in self.byid.items()};self.trail=[]
    def view(self):
        frontier=sorted(q for q in self.required if self.totals[q]<1);edges={str(q):sorted(k for k in self.incident[q] if self.valid[k] is None) for q in frontier};nodes=sorted({k for ids in edges.values() for k in ids})
        if any(not ids for ids in edges.values()):action='dead'
        elif any(len(ids)==1 for ids in edges.values()):action='forced'
        elif frontier:action='branch'
        else:action='exact'
        point=None
        if action in ['forced','branch']:
            choices=[q for q in frontier if action!='forced' or len(edges[str(q)])==1];point=min(choices,key=lambda q:(self.generations[q],len(edges[str(q)]),q))
        return dict(frontier=[list(q) for q in frontier],edges=edges,nodes=nodes,action=action,selected_point=list(point) if point else None,root_generations=[[q[0],q[1],self.generations[q]] for q in sorted(self.required)])
    def snapshot(self):return copy.deepcopy((self.totals,self.marks,self.mark_counts,self.selected,self.placement_generations,self.valid,self.generations))
    def place(self,key):
        require(self.valid.get(key,'missing') is None,'point-legal placement')
        self.trail.append(self.snapshot());p=self.byid[key];self.selected.add(key)
        generation=1+min(self.generations[(x,y)] for x,y,v in p['t'] if v>0);self.placement_generations[key]=generation
        for x,y,v in p['t']:self.totals[(x,y)]=self.totals.get((x,y),0)+v
        for x,y,v in p['m']:self.marks[(x,y)]=v;self.mark_counts[(x,y)]=self.mark_counts.get((x,y),0)+1
        affected={key}
        for q in self.reverse[key]:affected.update(self.dependencies[q])
        for k in affected:self.valid[k]=compatible(self.byid[k],self.totals,self.marks,self.selected)
    def undo(self):
        require(bool(self.trail),'rollback trail');self.totals,self.marks,self.mark_counts,self.selected,self.placement_generations,self.valid,self.generations=self.trail.pop()

def tiny():
    return compile_rows([dict(name='same0',family='tiny',premises=[['atom',0]],conclusion=['atom',0],dependencies=[]),dict(name='same1',family='tiny',premises=[['atom',1]],conclusion=['atom',1],dependencies=[]),dict(name='duplicate',family='tiny',premises=[['atom',0],['atom',0]],conclusion=['atom',1],dependencies=[]),dict(name='ordered',family='tiny',premises=[['atom',0],['atom',1]],conclusion=['atom',0],dependencies=[])],[dict(name='zero',kind='assumption',formula=['atom',0]),dict(name='one',kind='assumption',formula=['atom',1])],3)
