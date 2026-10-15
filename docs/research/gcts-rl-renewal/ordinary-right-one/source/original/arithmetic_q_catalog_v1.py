"""SOURCE ONLY complete explicitly restricted Q catalog; no proof route.

Caller injects exact QChecker module; no project import, search or target-backcone
selection. Every rule in the declared finite grammar is retained. Overflow is
UNKNOWN before a catalogue is returned. This is not full FOL/PA completeness.
"""
import copy
import hashlib
import itertools
import json
import time

VERSION='arithmetic-empty-Gamma-unary-generalize-finite-catalog-v1'
MARKING='injective-formula-ordered-primitive-offset-Q-v1'

def text(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def sha(value):return hashlib.sha256(text(value).encode()).hexdigest()
def require(ok,label):
    if not ok:raise ValueError(label)

def tick(deadline):
    if time.perf_counter()>=deadline:raise TimeoutError('complete Q catalogue unresolved')

def subformulas(formula):
    yield formula
    if formula[0]=='all':yield from subformulas(formula[2])
    elif formula[0] in ('not','imp','and','or'):
        for child in formula[1:]:yield from subformulas(child)

def subterms(term):
    yield term
    if term[0]=='fun':
        for child in term[2]:yield from subterms(child)

def terms(functions,parameters,bound,deadline):
    layers={1:{text(['var',v]):['var',v] for v in parameters}}
    layers[1].update({text(['fun',f,[]]):['fun',f,[]] for f,a in functions.items() if a==0})
    for size in range(2,bound+1):
        layer={}
        for function,arity in sorted(functions.items()):
            if arity==0:continue
            for partition in itertools.product(range(1,size),repeat=arity):
                if sum(partition)!=size-1:continue
                for children in itertools.product(*(layers[n].values() for n in partition)):
                    tick(deadline);term=['fun',function,list(children)];layer[text(term)]=term
        layers[size]=layer
    union={k:v for layer in layers.values() for k,v in layer.items()}
    return union

def prepare(spec,*,kernel_module,source_bindings,deadline):
    started=time.perf_counter();tick(deadline)
    fields={'schema','theory','ordered_Gamma','target','parameters','height','grammar','limits'}
    require(type(spec) is dict and set(spec)==fields and spec['schema']=='arithmetic-empty-Gamma-Q-declaration-v1','exact Q declaration')
    require(spec['ordered_Gamma']==[] and spec['height']==24,'genuine empty context, unchanged complete twenty-four rows')
    grammar={'term_node_bound':3,'target_and_axiom_open_subterms':True,'instantiation_rounds':2,
        'hole_context_node_bound':2,'equality_template_other_terms':'complete_operand_pool',
        'equality_operand_pairs':'all_ordered_pairs','generalization_sources':'all_resulting_parameter_scoped_equality_atoms',
        'target_seed_is_formula_only':True}
    require(spec['grammar']==grammar,'entire prospective restricted grammar, no outcome-selected alternatives')
    limits=spec['limits'];require(limits=={'maximum_formulas':50000,'maximum_recipes':20000,'maximum_visits':5000000},'fixed bounded preparation ceilings')
    checker=kernel_module.QChecker(spec['theory'],spec['parameters'],[],deadline=deadline,maximum_visits=limits['maximum_visits'])
    checker.formula(spec['target']);require(not checker.free(spec['target']),'closed unchanged target')
    require(len(spec['parameters'])==1 and spec['theory']['schemas']==[] and spec['theory']['predicates']=={},'first Q singleton parameter/equality-only signature scope')
    parameter=spec['parameters'][0]
    operands=terms(spec['theory']['functions'],spec['parameters'],grammar['term_node_bound'],deadline)
    basis={};recipes={};zero_roots=[]
    def add_formula(formula):
        checker.formula(formula)
        require(checker.free(formula)<=set(spec['parameters']),'declared intermediate free parameters')
        basis[text(formula)]=copy.deepcopy(formula)
        if len(basis)>limits['maximum_formulas']:raise TimeoutError('complete formula registry exceeds declared ceiling')
    def add_tree(formula):
        # Internal subformulas with outside free binder names are not in this
        # grammar. They remain literal subtrees of closed named axioms; omission
        # is a declared parameter-scope restriction, never full-FOL completeness.
        for sub in subformulas(formula):
            if checker.free(sub)<=set(spec['parameters']):add_formula(sub)
    def add_recipe(witness,premises):
        tick(deadline)
        command=copy.deepcopy(witness)
        if witness['rule']=='mp':command.update(antecedent=0,implication=1)
        elif witness['rule']=='generalize':command.update(source=0)
        checker.command(command,premises)
        raw={'primitive_witness':copy.deepcopy(witness),'ordered_premise_formulas':copy.deepcopy(premises)}
        recipes[text(raw)]=raw
        if len(recipes)>limits['maximum_recipes']:raise TimeoutError('complete primitive grammar exceeds declared ceiling')
        add_tree(witness['formula'])
    for formula in [spec['target'],*spec['theory']['axioms'].values()]:
        checker.formula(formula);add_tree(formula)
        for atomic in subformulas(formula):
            if atomic[0]=='eq':
                for value in atomic[1:]:
                    for term in subterms(value):
                        if checker.term_names(term)<=set(spec['parameters']):operands[text(term)]=copy.deepcopy(term)
    operand_values=[operands[k] for k in sorted(operands)]
    for label,formula in sorted(spec['theory']['axioms'].items()):add_recipe({'rule':'axiom','name':label,'formula':formula},[])
    round_census=[]
    for round_index in range(grammar['instantiation_rounds']):
        universals=[f for _,f in sorted(basis.items()) if f[0]=='all'];before=len(recipes)
        for universal in universals:
            for term in operand_values:
                instance=checker.substitute(universal[2],universal[1],term)
                add_recipe({'rule':'instantiate','formula':['imp',universal,instance],'universal':universal,'term':term},[])
        round_census.append({'round':round_index,'universals':len(universals),'new_recipes':len(recipes)-before,'recipes':len(recipes)})
    # Choose an unused literal hole without target or outcome inspection.
    used=set(spec['parameters'])
    for f in [spec['target'],*spec['theory']['axioms'].values()]:used|=checker.free(f,True)
    suffix=0
    while 'hole'+str(suffix) in used:suffix+=1
    hole='hole'+str(suffix);contexts=[['var',hole]]
    contexts.extend(['fun',function,[['var',hole]]] for function,arity in sorted(spec['theory']['functions'].items()) if arity==1)
    templates={}
    for context,other,side in itertools.product(contexts,operand_values,(0,1)):
        formula=['eq',context,other] if side==0 else ['eq',other,context];templates[text(formula)]=formula
    equality_census=0
    for _,template in sorted(templates.items()):
        for left,right in itertools.product(operand_values,repeat=2):
            result=['imp',['eq',left,right],['imp',checker.substitute(template,hole,left),checker.substitute(template,hole,right)]]
            add_recipe({'rule':'eq_subst','formula':result,'variable':hole,'template':template,'left':left,'right':right},[]);equality_census+=1
    atoms=[f for _,f in sorted(basis.items()) if f[0]=='eq']
    for atom in atoms:
        add_recipe({'rule':'generalize','variable':parameter,'formula':['all',parameter,atom]},[atom])
    # All implication formulas in this now closed finite basis expose ordered
    # MP, including generalization subtrees. No target backcone/filter is used.
    implications=[f for _,f in sorted(basis.items()) if f[0]=='imp']
    for implication in implications:
        add_recipe({'rule':'mp','formula':implication[2]},[implication[1],implication])
    formula_codes=[basis[k] for k in sorted(basis)];registry=sha(formula_codes)
    codes={text(f):i for i,f in enumerate(formula_codes)}
    context={'theory':copy.deepcopy(spec['theory']),'ordered_local_premises':[]}
    authority_data={'activated':False,'native_accepted':False,'recipient_theory_sha256':sha(spec['theory']),
        'profile':VERSION,'declaration_sha256':sha(spec),'scope':'Q finite six-rule open-parameter grammar only',
        'source_bindings':copy.deepcopy(source_bindings)}
    authority=dict(authority_data,epoch=sha(authority_data))
    records=[]
    for _,raw in sorted(recipes.items()):
        tick(deadline);preimage={'recipe':raw,'primitive_authority_epoch':authority['epoch'],
            'recipient_theory_sha256':authority['recipient_theory_sha256'],'marking_version':MARKING,
            'formula_registry_sha256':registry,'local_context_id':sha(context)}
        records.append(dict(raw,id='primitive-recipe-'+sha(preimage),identity_preimage=preimage))
    target_code=codes[text(spec['target'])]
    arity_counts={str(a):sum(len(r['ordered_premise_formulas'])==a for r in records) for a in (0,1,2)}
    # Exact unconstrained full placement universe, independently check later.
    raw_placements=sum(int(arity_counts['0'])+int(arity_counts['1'])*r+int(arity_counts['2'])*r*r for r in range(24))
    result={'schema':VERSION,'declaration':copy.deepcopy(spec),'context':context,'authority':authority,
        'formula_codes':formula_codes,'formula_registry_sha256':registry,'recipes':records,'height':24,
        'boundary':{'required':[[0,r] for r in range(24)],'roots':[0]*24,'seed_keys':[],
            'fixed_marks':[[1,r,-1] for r in range(-23,0)]+[[1,23,target_code]]},
        'census':{'operands':len(operand_values),'hole_contexts':len(contexts),'atomic_templates':len(templates),
            'generated_equality_schemes_before_dedup':equality_census,'formulas':len(formula_codes),
            'recipes':len(records),'arity_counts':arity_counts,'unconstrained_key_universe_upper_bound':raw_placements,
            'instantiation_rounds':round_census,'generalization_sources':len(atoms)},
        'first_primitive_search_accepted':False,'independent_catalogue_accepted':False,
        'native_accepted':False,'full_PA_accepted':False,'universal_compiler_accepted':False,
        'build_seconds_before_final_guard':time.perf_counter()-started}
    text(result);tick(deadline);return result
