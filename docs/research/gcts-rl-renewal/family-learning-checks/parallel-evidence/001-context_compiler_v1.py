"""Versioned recipient-context compiler. SOURCE ONLY until ROOT dispatch.

Retains the inactive, theory-bound primitive authority and all non-assumption
records. New recipient assumptions have fresh contextual licenses. No graph,
checker or production module is imported here; future callers pass pinned core
and lifecycle modules. Prior finite receipts are provenance, not new acceptance.
"""
import copy
import hashlib
import json
import time

VERSION = 'closed-recipient-context-transfer-v1'

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()

def integer(value):
    if type(value) is not int:raise ValueError('exact integer required')
    return value

def compile_context(source, spec, source_bindings, source_pins):
    """Compile exact new Gamma, not a seed mutation of an old graph.

    No target proof or chosen family names/sequence is consulted. The theory,
    formula registry, recipe positions, orientations and 24-row boundary are
    kept literal. All recipe identities are independently reconstructed here.
    """
    started=time.perf_counter()
    if len(source['formula_codes'])!=217 or len(source['recipes'])!=229:
        raise ValueError('complete original finite palette required')
    codes={canonical(f):i for i,f in enumerate(source['formula_codes'])}
    if len(codes)!=217 or digest(source['formula_codes'])!=source['formula_registry_sha256']:
        raise ValueError('injective exact formula registry')
    old=next(m for m in source['models'] if m['height']==24)
    old_context=old['context']
    if (old_context['theory']!=spec['theory_ast'] or old_context['ordered_local_premises']!=spec['original_ordered_hypotheses_ast']
            or old['context_id']!=digest(old_context)):
        raise ValueError('exact source context/theory required')
    premises=copy.deepcopy(spec['new_ordered_hypotheses_ast'])
    if len(premises)!=3 or premises[0]!=old_context['ordered_local_premises'][0] or premises[2]!=old_context['ordered_local_premises'][2]:
        raise ValueError('only hypothesis occurrence one may change')
    if premises[1]!=['eq',['fun','m',[]],['fun','n',[]]]:
        raise ValueError('declared equality premise only')
    if [codes.get(canonical(f)) for f in premises]!=[11,42,52] or codes.get(canonical(spec['target_ast']))!=54:
        raise ValueError('literal target and new premise registry relation')
    context={'theory':copy.deepcopy(old_context['theory']),'ordered_local_premises':premises}
    context_id=digest(context)
    authority=copy.deepcopy(source['authority'])
    if authority.get('activated') is not False or authority.get('native_accepted') is not False or digest({k:v for k,v in authority.items() if k!='epoch'})!=authority['epoch']:
        raise ValueError('inactive exact primitive theory authority required')
    if authority['recipient_theory_sha256']!=digest(context['theory']):
        raise ValueError('recipient theory binding differs')
    recipes=[];licenses=[];assumption_indices={};ids=set();non_assumptions=0
    for index,raw in enumerate(source['recipes']):
        item=copy.deepcopy(raw);w=item['primitive_witness'];ports=item['ordered_premise_formulas']
        original_pre={'recipe':{'primitive_witness':w,'ordered_premise_formulas':ports},
            'primitive_authority_epoch':authority['epoch'],'recipient_theory_sha256':authority['recipient_theory_sha256'],
            'marking_version':'injective-formula-ordered-mp-offset-v1','formula_registry_sha256':source['formula_registry_sha256']}
        is_assumption=w['rule']=='assumption'
        if is_assumption:original_pre['local_context_id']=old['context_id']
        if raw['identity_preimage']!=original_pre or raw['id']!='primitive-recipe-'+digest(original_pre):
            raise ValueError('source recipe identity/witness was not exact')
        if is_assumption:
            k=integer(w['index'])
            if k not in (0,1,2) or k in assumption_indices or ports or w['formula']!=old_context['ordered_local_premises'][k]:
                raise ValueError('one literal occurrence license per ordered hypothesis')
            assumption_indices[k]=index
            item['primitive_witness']={'rule':'assumption','index':k,'formula':copy.deepcopy(premises[k])}
            item['ordered_premise_formulas']=[]
            pre=copy.deepcopy(original_pre);pre['recipe']['primitive_witness']=copy.deepcopy(item['primitive_witness']);pre['local_context_id']=context_id
            item['identity_preimage']=pre;item['id']='primitive-recipe-'+digest(pre)
        else:
            non_assumptions+=1
            if item!=raw:raise AssertionError('non-assumption record changed')
            if w['rule'] not in ('axiom','instantiate','eq_subst','mp'):raise ValueError('unsupported logical witness')
        if item['id'] in ids:raise ValueError('duplicate new recipe identity')
        ids.add(item['id'])
        if canonical(item['primitive_witness']['formula']) not in codes or any(canonical(f) not in codes for f in ports):
            raise ValueError('complete licensed interface must lie in exact registry')
        recipes.append(item)
        licenses.append({'index':index,'kind':'fresh_context_assumption' if is_assumption else 'literal_non_assumption_source_record',
            'old_recipe_id':raw['id'],'new_recipe_id':item['id'],'source_record_sha256':digest(raw),
            'new_record_sha256':digest(item),'primitive_witness_sha256':digest(item['primitive_witness']),
            'ordered_premise_sha256':digest(ports),'native_accepted':False,
            'fresh_independent_acceptance':'pending; old audit binds source witness only'})
    if non_assumptions!=226 or set(assumption_indices)!={0,1,2}:
        raise ValueError('entire 226+3 palette required')
    boundary=copy.deepcopy(old['boundary'])
    if boundary['required']!=[[0,r] for r in range(24)] or boundary['root_generations']!=[[0,r,0] for r in range(24)] or boundary['fixed_exterior_m']!=[[1,r,-1] for r in range(-23,0)] or boundary['fixed_target_m']!=[[1,23,54]]:
        raise ValueError('unchanged complete point boundary required')
    boundary['fixed_initial_local_seeds']=[{'recipe_id':recipes[assumption_indices[k]]['id'],'row':k,'generation':0} for k in range(3)]
    return {'schema':VERSION,'status':'compiled_fresh_recipient_context_pending_independent_validation',
        'height':24,'context':context,'context_id':context_id,'source_context_id':old['context_id'],
        'theory':copy.deepcopy(context['theory']),'target':copy.deepcopy(spec['target_ast']),
        'formula_codes':copy.deepcopy(source['formula_codes']),'formula_registry_sha256':source['formula_registry_sha256'],
        'authority':authority,'primitive_authority_epoch_policy':'Exact inactive theory-bound source authority retained; recipient context/assumption/model/full-placement/body/pool bindings rebuilt.',
        'recipes':recipes,'recipe_licenses':licenses,'assumption_recipe_indices':[assumption_indices[k] for k in range(3)],
        'boundary':boundary,'orientation':'identity','marking_version':'injective-formula-ordered-mp-offset-v1',
        'source_bindings':copy.deepcopy(source_bindings),'source_pins':copy.deepcopy(source_pins),
        'non_assumption_records_preserved_verbatim':226,'compiler_seconds':time.perf_counter()-started,
        'native_queries':0,'native_accepted':False,'model_constructed_by_compile_context':False,
        'scope':'Authored exact context compilation; no proof search or logical checker acceptance.'}

def construct_graph(compiled,core):
    """Future gated model construction, three licensed gen-0 seeds only."""
    if compiled['schema']!=VERSION or compiled['status']!='compiled_fresh_recipient_context_pending_independent_validation':
        raise ValueError('exact compiler output required')
    if compiled['marking_version']!=core.MARKING_VERSION or compiled['orientation']!='identity':raise ValueError('same point grammar required')
    seeds=tuple(core.Key(index,k) for k,index in enumerate(compiled['assumption_recipe_indices']))
    g=core.PointGraph(height=24,formulas=compiled['formula_codes'],recipe_data=compiled['recipes'],
        context=compiled['context'],authority=compiled['authority'],fixed_marks=compiled['boundary']['fixed_exterior_m']+compiled['boundary']['fixed_target_m'],
        roots=[0]*24,seed_keys=seeds,source_bindings=compiled['source_bindings'])
    if g.context_id!=compiled['context_id'] or g.registry_sha!=compiled['formula_registry_sha256'] or [g.recipes[k.recipe].output for k in g.initial_selected]!=[11,42,52]:
        raise ValueError('new complete context seed relation differs')
    return g

def construct_family_authority(graph,projection,life,source_pins):
    """All 171 conditional source bodies, never canonical seed assumptions.

    Theory-bound primitive recipe IDs used by bodies are preserved; their full
    decorated placement/context identities are reconstructed by BodyAuthority.
    Only source native/independent receipts are inherited as provenance.
    """
    core=life.core
    if projection['formula_codes']!=graph.formulas or projection['authority_epoch']!=graph.authority_epoch or projection['native_accepted'] is not False:
        raise ValueError('exact theory-source projection relation required')
    bodies=[]
    for d in projection['definitions']:
        b={'kind':'finite_source_body_structurally_certified_not_native_accepted','name':d['name'],
            'canonical_input_rows':copy.deepcopy(d['canonical_input_rows']),'premise_codes':copy.deepcopy(d['premise_codes']),
            'primitive_members':[{k:copy.deepcopy(m[k]) for k in ('row','recipe_id','formula_code','ordered_inputs')} for m in d['primitive_members']],
            'source_body_sha256':d['source_body_sha256'],'mapped_body_sha256':d['mapped_body_sha256'],
            'dependency_bindings':[],'native_accepted':False,
            'earlier_expansion_closure':'all recursive source dependencies in pinned full expansion and its prior independent audit; fresh recipient projection pending independent audit',
            'full_frozen_definition_sha256':core.digest(d)}
        for member in b['primitive_members']:
            recipe=graph.recipes[graph.recipe_index[member['recipe_id']]]
            if recipe.witness['rule']=='assumption':raise ValueError('source-local aliases cannot become global recipient assumption recipes')
        b['ordered_receptor_ports']=life.receptor_ports(b,graph);bodies.append(b)
    if len(bodies)!=171 or len({b['name'] for b in bodies})!=171:raise ValueError('entire 171 distinct declarations required')
    unique={}
    for p in source_pins:
        q={k:p[k] for k in ('path','sha256','bytes')}
        if q['path'] in unique and unique[q['path']]!=q:raise ValueError('inconsistent source pin alias')
        unique[q['path']]=q
    return life.BodyAuthority.build(graph,[unique[p] for p in sorted(unique)],bodies)
