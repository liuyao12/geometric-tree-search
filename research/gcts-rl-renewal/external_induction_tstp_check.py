"""Full shared-context TSTP adapter for a strictly scoped first-order fragment.

Inputs are original-AST bound. Every ordinary local consequence has a replayed
propositional or finite Herbrand/EUF refutation. A separate exact conservative
witness extension is permitted for an isolated closed-FOF Skolem step or a
restricted unary compact annotation, with explicit reconstructed intermediates.
The original published checker and standalone prototype remain unchanged.
Unsupported transformations and incomplete local refutations fail closed.
"""
import copy,functools,itertools,signal,time
from external_prover_check import alpha,closed,entails,free,leaves,native_formula,nnf,records,replay_refutation,grounding,substitute,symbol_names,validate_signature
from external_prover_inputs import canonical,sha
from external_induction_skolem import check_extension,witness_sites

def frozen(x):return tuple(frozen(a) for a in x) if isinstance(x,list) else x

def bounded_step(function):
    """Unix single-worker thirty-second bound on each logical check/replay."""
    @functools.wraps(function)
    def call(*args,**kwargs):
        def stop(signum,frame):raise TimeoutError('local certificate step exceeds thirty-second wall bound')
        previous=signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,30)
        try:return function(*args,**kwargs)
        finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)
    return call

def proposition(parents,child):
    """Uniform propositional abstraction, retaining quantifiers as whole atoms."""
    atoms={}
    def convert(f):
        h=f[0]
        if h in ('top','bot'):return f
        if h in ('not','and','or','imp'):return (h,*(convert(a) for a in f[1:]))
        if h not in ('forall','exists','pred','eq'):raise ValueError('unsupported proposition atom')
        k=canonical(alpha(f))
        if k not in atoms:atoms[k]='abstract'+str(len(atoms))
        return ('pred',atoms[k],())
    translated=[convert(f) for f in [*parents,child]]
    check=entails(translated[:-1],translated[-1])
    return dict(method='uniform_propositional_abstraction',atoms=atoms,translated=translated,check=check)

@bounded_step
def consequence(parents,child):
    """A stronger certificate is required before any relation is accepted."""
    began=time.perf_counter();parents=[closed(p) for p in parents];child=closed(child)
    p=proposition(parents,child)
    if p['check']['status']=='checked':return dict(status='checked',seconds=time.perf_counter()-began,certificate=p)
    # NNF equality allows bound-name changes, with all lexical scopes retained.
    for i,f in enumerate(parents):
        if alpha(nnf(f))==alpha(nnf(child)):
            return dict(status='checked',seconds=time.perf_counter()-began,certificate=dict(method='exact_alpha_NNF_equivalence',parent=i,normal_form=alpha(nnf(child))))
    check=entails(parents,child)
    if check['status']!='checked':raise ValueError('local consequence remains unknown')
    return dict(status='checked',seconds=time.perf_counter()-began,certificate=dict(method='finite_Herbrand_EUF_refutation',check=check))

@bounded_step
def replay_consequence(parents,child,result):
    """Reconstruct abstraction/ground instances and replay the actual tree."""
    if result.get('status')!='checked':raise ValueError('unaccepted consequence')
    parents=[closed(p) for p in parents];child=closed(child);cert=result['certificate'];method=cert['method']
    if method=='exact_alpha_NNF_equivalence':
        i=cert['parent']
        if type(i) is not int or not 0<=i<len(parents) or alpha(nnf(parents[i]))!=alpha(nnf(child)) or canonical(cert['normal_form'])!=canonical(alpha(nnf(child))):raise ValueError('NNF equivalence certificate')
    else:
        if method=='uniform_propositional_abstraction':
            # Reconstruct directly instead of trusting saved translated formulas.
            atoms={}
            def abstract(f):
                if f[0] in ('top','bot'):return f
                if f[0] in ('not','and','or','imp'):return (f[0],*(abstract(a) for a in f[1:]))
                k=canonical(alpha(f));n=atoms.setdefault(k,'abstract'+str(len(atoms)));return ('pred',n,())
            fs=[abstract(f) for f in [*parents,child]]
            if atoms!=cert['atoms'] or canonical(fs)!=canonical(cert['translated']):raise ValueError('propositional abstraction binding')
            check=cert['check'];premises=fs[:-1];goal=fs[-1]
        elif method=='finite_Herbrand_EUF_refutation':check=cert['check'];premises=parents;goal=child
        else:raise ValueError('unknown local certificate method')
        if check['status']!='checked':raise ValueError('unchecked local certificate')
        clauses,pool=grounding(premises+[('not',goal)])
        if check['ground_clauses']!=len(clauses) or check['ground_terms']!=len(pool):raise ValueError('local grounding census')
        replay=copy.deepcopy(check['refutation']);replay['atoms']=[frozen(a) for a in replay['atoms']]
        replay_refutation(clauses,replay)
    return True

def reconstruct_witnesses(parent,child):
    """Recover proposed fresh names from the AST; prototype checks the proposal."""
    parent=closed(parent);child=closed(child);sites=witness_sites(parent);names={}
    def term(p,c,env,universals):
        if p[0]=='var':
            value=env[p[1]]
            if value[0]=='witness':
                path=value[1];args=value[2]
                if c[0]!='fun' or c[2]!=args:raise ValueError('witness term/dependency mismatch')
                if path in names and names[path]!=c[1]:raise ValueError('inconsistent witness occurrence')
                names[path]=c[1]
            elif c!=value:raise ValueError('universal variable/capture mismatch')
        elif p[0]=='fun':
            if c[0]!='fun' or p[1]!=c[1] or len(p[2])!=len(c[2]):raise ValueError('original function changed')
            for a,b in zip(p[2],c[2]):term(a,b,env,universals)
        else:raise ValueError('unsupported witness term')
    def walk(p,c,path,env,universals):
        h=p[0]
        if h=='exists':return walk(p[2],c,path+(2,),{**env,p[1]:('witness',path,tuple(universals))},universals)
        if c[0]!=h:raise ValueError('Skolem connective/quantifier mismatch')
        if h=='forall':
            v=('var',c[1]);return walk(p[2],c[2],path+(2,),{**env,p[1]:v},universals+[v])
        if h in ('and','or'):
            walk(p[1],c[1],path+(1,),env,universals);walk(p[2],c[2],path+(2,),env,universals)
        elif h=='lit':
            if p[1]!=c[1] or p[2][0]!=c[2][0]:raise ValueError('Skolem literal polarity/type')
            a,b=p[2],c[2]
            if a[0]=='eq':
                term(a[1],b[1],env,universals);term(a[2],b[2],env,universals)
            elif a[0]=='pred':
                if a[1]!=b[1] or len(a[2])!=len(b[2]):raise ValueError('Skolem predicate changed')
                for t,u in zip(a[2],b[2]):term(t,u,env,universals)
            else:raise ValueError('unsupported Skolem atom')
        elif h not in ('top','bot'):raise ValueError('unsupported Skolem NNF')
    walk(nnf(parent),nnf(child),(),{},[])
    if any(tuple(s['path']) not in names for s in sites):raise ValueError('vacuous existential witness not explicitly reconstructible')
    return [dict(s,symbol=names[tuple(s['path'])]) for s in sites]

def status_esa(source):
    return any(isinstance(v,dict) and v.get('head')=='status' and v.get('args')==['esa'] for v in source['args'][1])

def compact_chain(source,parent_name):
    """Recognize a restricted unary annotation; labels alone prove nothing.

    The printed compound relation is certified by a separate explicit derivation
    from its exact named parent. We do not pretend to recover E's unprinted
    internal bound-variable names or each hidden implementation intermediate.
    """
    chain=[];skolems=0
    while isinstance(source,dict):
        if source.get('head')!='inference' or len(source.get('args',[]))!=3:raise ValueError('opaque compact preprocessing')
        rule,metadata,parents=source['args']
        if not isinstance(parents,list) or len(parents)!=1:raise ValueError('compact preprocessing must have one parent at each node')
        if rule in ('skolemize','fof_skolemize'):relation='esa';skolems+=1
        elif rule in ('fof_nnf','variable_rename','shift_quantors','distribute'):relation='thm'
        else:raise ValueError('unsupported compact preprocessing rule')
        if metadata!=[dict(head='status',args=[relation])]:raise ValueError('compact preprocessing relation annotation')
        chain.append(dict(rule=rule,relation=relation));source=parents[0]
    if source!=parent_name or skolems!=1:raise ValueError('compact preprocessing requires one named parent and one Skolem transformation')
    return chain

def from_nnf(f):
    if f[0]=='lit':return f[2] if f[1] else ('not',f[2])
    if f[0] in ('forall','exists'):return (f[0],f[1],from_nnf(f[2]))
    if f[0] in ('and','or'):return (f[0],from_nnf(f[1]),from_nnf(f[2]))
    if f[0] in ('top','bot'):return f
    raise ValueError('unsupported reconstructed NNF')

def witness_formula(parent,witnesses):
    """Propose the lexical witness formula; unchanged prototype certifies it."""
    by_path={tuple(w['path']):w for w in witnesses};counter=[0]
    def walk(f,path,env,universals):
        h=f[0]
        if h=='forall':
            v=('var','V'+str(counter[0]));counter[0]+=1
            return ('forall',v[1],walk(f[2],path+(2,),{**env,f[1]:v},universals+[v]))
        if h=='exists':return walk(f[2],path+(2,),{**env,f[1]:('fun',by_path[path]['symbol'],tuple(universals))},universals)
        if h in ('and','or'):return (h,walk(f[1],path+(1,),env,universals),walk(f[2],path+(2,),env,universals))
        if h=='lit':return ('lit',f[1],substitute(f[2],env))
        return f
    return from_nnf(walk(nnf(closed(parent)),(),{},[]))

def new_functions(child,signature):
    functions={};predicates=set()
    def visit(f):
        if f[0] in ('fun','pred'):
            declared=signature['function_arities'] if f[0]=='fun' else signature['predicate_arities']
            if f[1] not in declared:
                if f[0]=='pred':predicates.add(f[1])
                elif f[1] in functions and functions[f[1]]!=len(f[2]):raise ValueError('inconsistent introduced-function arity')
                else:functions[f[1]]=len(f[2])
            for t in f[2]:visit(t)
        else:
            for a in f[1:]:
                if isinstance(a,tuple):visit(a)
    visit(child)
    if predicates:raise ValueError('fresh predicates/definitions are unsupported')
    return functions

def compact_extension(parent,child,source,parent_name,signature,reserved,saved=None):
    """Check an explicit replacement derivation for a compact printed step.

    Search over at most six lexical existential/name assignments is generic and
    bounded. No theorem-specific path or unprinted E formula is trusted. The
    unchanged strict prototype checks every witness scope/freshness/dependency;
    a complete independent consequence certificate checks the displayed child.
    """
    chain=compact_chain(source,parent_name);parent=closed(parent);child=closed(child)
    sites=witness_sites(parent);functions=new_functions(child,signature)
    if not sites or len(sites)!=len(functions) or len(sites)>6:raise ValueError('unsupported compact witness occurrence count')
    if set(functions)&set(reserved):raise ValueError('compact witness is not globally fresh')
    normalized=from_nnf(nnf(parent))
    if saved is None:normalization=consequence([parent],normalized)
    else:
        normalization=saved['normalization'];replay_consequence([parent],normalized,normalization)
    assignments=[saved['witnesses']] if saved is not None else [
        [dict(site,symbol=name) for site,name in zip(sites,names)]
        for names in itertools.permutations(sorted(functions))
        if all(functions[name]==len(site['dependencies']) for site,name in zip(sites,names))]
    errors=[]
    for witnesses in assignments:
        intermediate=witness_formula(parent,witnesses)
        extension=check_extension(parent,intermediate,witnesses,signature,reserved)
        if extension['introduced_functions']!=functions:raise ValueError('compact introduced-function census')
        validate_signature(child,{**signature,'function_arities':{**signature['function_arities'],**functions}})
        if saved is None:
            try:postprocessing=consequence([intermediate],child)
            except (ValueError,TimeoutError) as e:errors.append(str(e));continue
        else:
            postprocessing=saved['postprocessing'];replay_consequence([intermediate],child,postprocessing)
        result=dict(status='checked_reconstructed_compact_context_extension',annotation_chain=chain,
                    normalized_parent=normalized,normalization=normalization,witnesses=witnesses,
                    witness_formula=intermediate,extension=extension,postprocessing=postprocessing,
                    reconstruction_scope='Explicit alternative certificate for the printed parent-to-child compound relation. The pre-Skolem NNF, strict lexical witness formula and displayed-child consequence are checked; E\'s unprinted implementation intermediates are not asserted to be reconstructed verbatim.')
        if saved is not None and canonical(result)!=canonical(saved):raise ValueError('saved compact reconstruction binding')
        return result
    raise ValueError('compact displayed-child consequence remains unknown: '+repr(errors))

def check_output(output,mapping,input_path,saved=None):
    """Model-preserving shared context, exact inputs, no unchecked proof node."""
    began=time.perf_counter();rs=records(output);known={};checks=[];context=[];introductions={};conjectures=set();negations=set();inputs=[]
    expected={e['name']:(e,native_formula(e['formula'],mapping)) for e in mapping['entries']}
    if len(expected)!=len(mapping['entries']) or sum(e['role']=='conjecture' for e in mapping['entries'])!=1:raise ValueError('unique complete input inventory')
    original=set(mapping['function_arities'])|set(mapping['predicate_arities']);reserved=set(original)
    if any(n.startswith('__checker_') for n in original):raise ValueError('original symbol collides with reserved independent-grounding namespace')
    signature=dict(function_arities=copy.deepcopy(mapping['function_arities']),predicate_arities=copy.deepcopy(mapping['predicate_arities']))
    for e,f in expected.values():
        validate_signature(f,signature)
        if free(f):raise ValueError('original input must be explicitly closed')
        if e['role'] not in ('axiom','lemma','conjecture'):raise ValueError('unsupported original role')
    # Context starts with every exact non-conjecture input. Native/admitted
    # interface validity is an independent pre-run gate, not inferred here.
    context=[closed(f) for e,f in expected.values() if e['role']!='conjecture']
    if saved is not None and (saved['status']!='checked_complete_derivation' or len(saved['checks'])!=len(rs)):raise ValueError('saved complete certificate shape')
    for index,r in enumerate(rs):
        n=r['name'];s=r['source'];f=r['formula'];before=sha(canonical(context));registry_before=sha(canonical(introductions))
        if n in known:raise ValueError('duplicate proof node')
        if not isinstance(s,dict):raise ValueError('opaque source')
        if s.get('head')=='file':
            if len(s['args'])!=2 or s['args'][0]!=input_path or s['args'][1] not in expected:raise ValueError('input file/name identity')
            e,want=expected[s['args'][1]]
            validate_signature(f,signature)
            if r['role']!=e['role'] or alpha(f)!=alpha(want):raise ValueError('original input formula/role mismatch')
            if e['role']=='conjecture':conjectures.add(n)
            else:inputs.append(e['name'])
            result=dict(name=n,status='checked_input',original_name=e['original_name'])
        elif s.get('head')=='inference':
            ps=list(dict.fromkeys(leaves(s)))
            if any(p not in known for p in ps):raise ValueError('forward/missing proof parent')
            rule=s['args'][0];new=symbol_names(f)-set(signature['function_arities'])-set(signature['predicate_arities'])
            if rule=='assume_negation':
                if len(ps)!=1 or ps[0] not in conjectures or r['role']!='negated_conjecture' or alpha(nnf(closed(f)))!=alpha(nnf(closed(known[ps[0]]['formula']),False)):raise ValueError('incorrect target negation')
                if negations:raise ValueError('repeated target-negation assumption')
                validate_signature(f,signature);negations.add(n);context.append(closed(f));result=dict(name=n,status='checked_negation',parents=ps,rule=rule)
            else:
                if any(p in conjectures for p in ps):raise ValueError('positive conjecture used as proof premise')
                if new:
                    if r['language']!='fof' or len(ps)!=1:raise ValueError('unsupported symbol-introducing transformation')
                    parent=closed(known[ps[0]]['formula']);child=closed(f)
                    isolated=rule=='fof_skolemize' and len(s['args'][2])==1 and s['args'][2][0]==ps[0] and status_esa(s)
                    reconstruction=None
                    if isolated:
                        witnesses=reconstruct_witnesses(parent,child);extension=check_extension(parent,child,witnesses,signature,reserved)
                    else:
                        prior=saved['checks'][index] if saved is not None else None
                        if prior is not None and (prior.get('name')!=n or prior.get('parents')!=ps or prior.get('rule')!=rule or prior.get('status')!='checked_conservative_context_extension'):raise ValueError('saved compact consequence identity')
                        reconstruction=compact_extension(parent,child,s,ps[0],signature,reserved,saved=prior.get('reconstruction') if prior is not None else None)
                        extension=reconstruction['extension'];witnesses=reconstruction['witnesses']
                    if set(extension['introduced_functions'])!=new:raise ValueError('introduced-symbol census')
                    for symbol,arity in extension['introduced_functions'].items():
                        signature['function_arities'][symbol]=arity;reserved.add(symbol);introductions[symbol]=dict(node=n,arity=arity,witness=next(w for w in witnesses if w['symbol']==symbol))
                    result=dict(name=n,status='checked_conservative_context_extension',parents=ps,rule=rule,extension=extension)
                    if reconstruction is not None:
                        # The synthetic witness formula is an actual intermediate
                        # in the checked replacement derivation and shared context.
                        context.append(frozen(reconstruction['witness_formula']));result['reconstruction']=reconstruction
                else:
                    validate_signature(f,signature);parents=[closed(known[p]['formula']) for p in ps]
                    if saved is None:proof=consequence(parents,closed(f))
                    else:
                        prior=saved['checks'][index]
                        if prior.get('name')!=n or prior.get('parents')!=ps or prior.get('rule')!=rule or prior.get('status')!='checked_logical_consequence':raise ValueError('saved local consequence identity')
                        proof=prior['proof'];replay_consequence(parents,closed(f),proof)
                    result=dict(name=n,status='checked_logical_consequence',parents=ps,rule=rule,proof=proof)
                context.append(closed(f))
        else:raise ValueError('introduced/opaque source is unsupported')
        result.update(context_before_sha256=before,registry_before_sha256=registry_before,context_size=len(context),context_after_sha256=sha(canonical(context)),registry_after_sha256=sha(canonical(introductions)))
        if saved is not None:
            prior=saved['checks'][index]
            # Times are copied for local certificates; all binding and structural
            # extension fields are reconstructed, rather than trusted on replay.
            if canonical(prior)!=canonical(result):raise ValueError('saved shared-context certificate mismatch')
        checks.append(result);known[n]=r
    if not rs or rs[-1]['formula']!=('bot',) or not negations:raise ValueError('no complete contradiction from negated target')
    result=dict(status='checked_complete_derivation',steps=len(rs),checks=checks,introductions=introductions,checked_input_count=len(inputs),used_lemma_inputs=[n for n in inputs if expected[n][0]['role']=='lemma'],original_input_count=len(mapping['entries']),seconds=time.perf_counter()-began,
                scope='Every listed input, transformation and logical inference is checked. A single shared context preserves model existence through globally fresh exact Skolem extensions. Logical steps have independently replayable propositional/Herbrand-EUF certificates. No native Wang acceptance is claimed.')
    if saved is not None:
        for field in ('steps','introductions','checked_input_count','used_lemma_inputs','original_input_count'):
            if canonical(saved[field])!=canonical(result[field]):raise ValueError('saved overall proof census mismatch')
    return result
