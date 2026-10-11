"""Independent checks of prefix teachers and their bounded causal restriction.

Imports none of the new learner or overlay. Reuses the independently authored
Notebook 63 literal-domain and complete-tree checker, not its producer engine.
"""
import collections,itertools,json
from audit_semantic_inventory import rebuild,guided_tree,need,same,pin,packed,encode

def decorations(c):return json.dumps(dict(occupancy=c['occupancy'],marks=c['marks']),sort_keys=True,separators=(',',':'))

def semantic(model):
    return {k:v for k,v in model.items() if k not in ('compile_seconds','encoding','scope','initial_marks','failure_overlay')}

def fixed_vocabulary_prefix(spec,compiled,registry):
    # The parent vocabulary stays fixed even if the new prefix target has
    # fewer subformulas. Recomputing it from that target would unsoundly omit
    # original prefix candidates, particularly in quantified examples.
    basis=compiled['basis'];variables=compiled['variables']
    definitions={d['name']:d for d in registry['definitions']}
    interfaces=[definitions[n] for n in registry['interfaces']]
    arity=max([len(d['definition']['premises']) for d in interfaces]+[0])
    modes={d['name']:i+1 for i,d in enumerate(interfaces)}
    placements=[];conflicts=[];domains=[];tauts={packed(f) for f in compiled['tautologies']}
    def add(key,entries,command,requirements,kind,**extra):
        marks={}
        for p,v in entries:
            if p in marks and marks[p]!=v:
                conflicts.append(dict(key=key,reason='internally unequal markings'));return
            marks[p]=v
        placements.append(dict(key=key,occupancy=[((4*key[0],key[1]),12)],marks=sorted(marks.items()),
            slot=key[0],kind=kind,command=command,requirements=requirements,**extra))
    for j in range(spec['length']):
        formulas=[spec['target']] if j+1==spec['length'] else basis;rows=[]
        for f in formulas:
            rows.extend(dict(rule='axiom',formula=f,name=name) for name in sorted(spec['theory']['axioms']))
            rows.extend(dict(rule='generalize',formula=f,variable=v,source=s) for v in variables for s in range(j))
            rows.extend(dict(rule='mp',formula=f,antecedent=a,implication=b) for a,b in itertools.product(range(j),repeat=2))
            rows.extend(dict(rule=r,formula=f) for r in ('refl','tautology'))
            rows.extend(dict(rule='block',formula=f,name=d['name']) for d in interfaces)
        rows.sort(key=lambda c:(c['rule'],packed(c['formula']),packed(c)));domains.append(rows)
        for k,c in enumerate(rows):
            f=c['formula'];r=c['rule'];mode=modes[c['name']] if r=='block' else 0
            entries=encode(j,'command',c)+encode(j,'formula',f)+[((4*j+2,90),mode)]
            add((j,0,k,0),entries,c,[],'command')
            if r=='mp':
                for v,imp in enumerate(basis):
                    if imp[0]=='imp' and imp[2]==f:
                        required=[(c['antecedent'],imp[1]),(c['implication'],imp)]
                        add((j,1,k,v),entries+[e for i,a in required for e in encode(i,'formula',a)],c,required,'guard')
            else:
                valid=False;required=[]
                if r=='axiom':valid=spec['theory']['axioms'][c['name']]==f
                elif r=='refl':valid=f[0]=='eq' and f[1]==f[2]
                elif r=='tautology':valid=packed(f) in tauts
                elif r=='generalize':
                    valid=f[0]=='all' and f[1]==c['variable']
                    if valid:required=[(c['source'],f[2])]
                elif r=='block':valid=definitions[c['name']]['definition']['conclusion']==f
                if valid:add((j,1,k,0),entries+[e for i,a in required for e in encode(i,'formula',a)],c,required,'guard')
        for r in range(arity):
            add((j,2+r,0,0),[((4*j+2,90),0),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=0,source=None)
            for d in interfaces:
                mode=modes[d['name']];premises=d['definition']['premises']
                if r>=len(premises):
                    add((j,2+r,mode,0),[((4*j+2,90),mode),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=mode,source=None)
                else:
                    for source in range(j):
                        required=[(source,premises[r])]
                        add((j,2+r,mode,source+1),[((4*j+2,90),mode),((4*j+2,100+r),source)]+encode(source,'formula',premises[r]),
                            None,required,'lemma_input',input=r,mode=mode,source=source)
    return dict(domains=domains,command_counts=list(map(len,domains)),arity=arity,mode_ids=modes,
        placements=sorted(placements,key=lambda c:c['key']),conflicts=conflicts,
        roots=[(4*j,r) for j in range(spec['length']) for r in range(2+arity)])

def bound_context(parent):
    return dict(theory=parent.spec['theory'],basis=parent.compiled['basis'],variables=parent.compiled['variables'],
        tautologies=parent.compiled['tautologies'],definitions=parent.inventory['definitions'],
        interfaces=parent.inventory['interfaces'],native_blocks=parent.inventory['native_blocks'],
        arity=parent.arity,mode_ids=parent.mode,
        encoding='Exact canonical command/formula words and strict earlier source ports; semantic-receptor model 001')

def teacher(parent,probe):
    spec=probe['spec'];original=parent.spec
    need(spec['theory']==original['theory'] and spec['length']==probe['slot']+1
         and spec['target']==probe['formula'],'declared prefix statement and theory')
    record=fixed_vocabulary_prefix(spec,parent.compiled,parent.inventory)
    need(same(semantic(record),semantic(probe['model'])),'independently rebuilt complete prefix inventory')
    full=rebuild(original,parent.compiled,parent.inventory)
    required={decorations(c):tuple(c['key']) for c in full['placements']
        if c['key'][0]<spec['length'] and not (c['key'][0]==probe['slot'] and c['key'][1]<2
                                               and c['command']['formula']!=probe['formula'])}
    pairs=[]
    for c in record['placements']:
        word=decorations(c);need(word in required,'necessary-prefix decorated placement')
        pairs.append((tuple(c['key']),required.pop(word)))
        need(all(p[0]<=4*c['key'][0]+2 for p,v in c['marks']),'all requirements stay at this row or earlier')
    need(not required and same(pairs,probe['lift']['pairs']) and pin(pairs)==probe['lift']['sha256'],
         'all original prefix placements and exact identity lift')
    need(record['roots']==[p for p in full['roots'] if p[0]<4*spec['length']],
         'complete prefix root restriction')
    checked=guided_tree(spec,record,probe['search'],parent.inventory,None)
    labels={'finite_marked_proof_region':'positive','exhausted_finite_marked_region':'negative',
            'unknown_search_budget':'unknown'}
    need(probe['label']==labels[probe['search']['status']],'unknown is never an exclusion')
    return dict(status='passed',label=probe['label'],lift_sha256=pin(pairs),**checked)

def check_learning(parent,learning):
    # Reconstruct the complete per-row formula catalog from initial native
    # target agreement. Do not trust a sampled teacher list or learner labels.
    full=rebuild(parent.spec,parent.compiled,parent.inventory);target=parent.spec['target']
    need(same(semantic(full),semantic(parent.record())),'actual parent inventory independently reconstructed')
    need(same(bound_context(parent),learning['context']) and pin(bound_context(parent))==learning['context_sha256'],
         'complete grammar context of every transferred prefix certificate')
    groups=collections.defaultdict(list);formulas={json.dumps(f,sort_keys=True,separators=(',',':'),ensure_ascii=False):f for f in parent.compiled['basis']}
    for c in full['placements']:
        if c['key'][1]!=0:continue
        if c['key'][0]+1==parent.spec['length'] and c['command']['formula']!=target:continue
        word=json.dumps(c['command']['formula'],sort_keys=True,separators=(',',':'),ensure_ascii=False)
        groups[c['key'][0],word].append(c['key'])
    catalog=[dict(id=i,slot=j,length=j+1,formula=formulas[word],command_keys=keys)
             for i,((j,word),keys) in enumerate(sorted(groups.items()))]
    need(same(catalog,learning['catalog']) and len(learning['probes'])==len(catalog),'complete prefix query catalog')
    counts=collections.Counter();nodes=0
    for expected,probe in zip(catalog,learning['probes']):
        for k,v in expected.items():need(same(probe[k],v),'unsampled prefix '+k)
        need(all(probe['search']['limits'][k]==v for k,v in learning['limits'].items()),'predeclared teacher budgets')
        checked=teacher(parent,probe);counts[checked['label']]+=1;nodes+=checked['nodes']
        if 'independent_check' in probe:need(probe['independent_check']==checked,'actual pre-activation check')
    need(dict(counts)==learning['counts'],'all resolved and unresolved prefix results')
    return dict(version='prefix-failure-certificate-001',status='passed',learning_sha256=pin(learning),
        context_sha256=learning['context_sha256'],prefixes=len(catalog),counts=dict(counts),nodes=nodes,
        scope='Independent reconstruction of every candidate and every visited domain, exact prefix restriction, complete fallback and rollback. Negatives authorize only grammar-scoped redundant marking values; unknowns authorize none.')
