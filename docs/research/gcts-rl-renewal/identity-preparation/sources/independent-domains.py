"""SOURCE ONLY independent initial point-domain audit for the full compact catalog.

Every factor is regenerated from all original negative-offset t/m placements,
not producer grouped counts or FactorStream helpers. Positive support is the
unit obligation (0,row); exterior assigned -1 excludes negative source rows.
The complete product factor plus alias-conflict condition describes every key.
No proof/search/core imports, calls or scheduler certification occur here.
"""
import hashlib
import json
import struct

MARKING = 'injective-formula-ordered-mp-offset-v1'
FACTOR = struct.Struct('<QQQBQ')


def need(condition, label):
    if not condition:
        raise ValueError(label)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',', ':'),
                      ensure_ascii=False,allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def initial_small_state(grammar, recipe_ids):
    """Exact original full small state, with independently rebuilt model epoch."""
    need(len(recipe_ids)==len(grammar.records) and len(set(recipe_ids))==len(recipe_ids),
         'complete unique original recipe identifiers')
    fixed=[[1,row,-1] for row in range(-23,0)]+[[1,23,grammar.target_code]]
    seeds=[[index,row,[]] for row,index in enumerate(grammar.assumptions)]
    preimage=dict(height=24,context=grammar.context,registry=grammar.registry_sha,
        authority=grammar.authority['epoch'],recipes=recipe_ids,fixed_marks=sorted(fixed),
        roots=[0]*24,seed_keys=seeds,marking_version=MARKING,fixture=False,
        source_bindings=grammar.source_bindings)
    h=hashlib.sha256();h.update(b'{')
    for ordinal,key in enumerate(sorted(preimage)):
        if ordinal:h.update(b',')
        h.update(canonical(key).encode('utf8'));h.update(b':')
        if key=='recipes':
            h.update(b'[')
            for index,identifier in enumerate(recipe_ids):
                if index:h.update(b',')
                h.update(canonical(identifier).encode('utf8'))
            h.update(b']')
        else:
            h.update(canonical(preimage[key]).encode('utf8'))
    h.update(b'}');epoch=h.hexdigest()
    marks={tuple(t[:2]):[t[2],1] for t in fixed}
    for row,formula in enumerate(grammar.gamma):
        code=grammar.codes[grammar.arena.intern(formula)]
        need((1,row) not in marks,'three seeds do not overwrite fixed exterior/target')
        marks[(1,row)]=[code,1]
    return dict(totals=[1,1,1]+[0]*21,
        marks=[[x,y,*values] for (x,y),values in sorted(marks.items())],
        order=seeds,selected_generations=[[k,0] for k in sorted(seeds)],
        roots=[0]*24,excluded=[[] for _ in range(24)],model_epoch=epoch)


def factors(grammar, row, state):
    """Independent complete literal-negative-offset factor generator.

    No geometry/semantic premise shortcut supplies degrees. Formula and input
    reference channel m-values alone remove candidates. Equal-code read ports
    may alias; different-code reads at one row conflict and are excluded.
    """
    need(type(row) is int and 0<=row<24,'exact required row')
    if state['totals'][row]:
        return
    marks={(x,y):value for x,y,value,_ in state['marks']}
    for index,record in enumerate(grammar.records):
        output=grammar.codes[record[1]]
        need(type(output) is int and output>=0,'injective nonnegative formula code')
        if (1,row) in marks and marks[(1,row)]!=output:
            continue
        if record[0]!='mp':
            yield [index,0,0,False,1]
            continue
        inputs=(grammar.codes[record[2]],grammar.codes[record[3]])
        allowed=[]
        for port,code in enumerate(inputs):
            refs=[]
            for offset in range(-23,0):
                source=row+offset
                if ((1,source) in marks and marks[(1,source)]!=code
                        or (2+port,row) in marks and marks[(2+port,row)]!=offset):
                    continue
                # All negative refs MUST be eliminated by exterior m=-1,
                # never an undeclared logical predecessor filter.
                need(0<=source<row,'complete exterior reduction to strict prior refs')
                refs.append(source)
            allowed.append(refs)
        different=inputs[0]!=inputs[1]
        # The two complete literal source sets above are still checked. Their
        # entire Cartesian product loses exactly the common diagonal when
        # distinct formula channels cannot occupy the same source point.
        count=len(allowed[0])*len(allowed[1])
        if different:
            count-=len(set(allowed[0]).intersection(allowed[1]))
        if count:
            yield [index,sum(1<<r for r in allowed[0]),sum(1<<r for r in allowed[1]),
                   different,count]


def factor_receipt(grammar, row, state):
    h=hashlib.sha256();n=0;total=0
    for index,left,right,different,count in factors(grammar,row,state):
        need(0<=left<1<<24 and 0<=right<1<<24 and type(different) is bool
             and type(count) is int and count>0,'exact complete positive factor fields')
        h.update(FACTOR.pack(index,left,right,int(different),count));n+=1;total+=count
    return dict(row=row,factor_count=n,bytes=n*33,sha256=h.hexdigest(),
                base_count=total,excluded_legal=[],count=total)


def audit_factor_receipts(grammar, state, claimed):
    need(type(claimed) is list and len(claimed)==24,'all required row receipts')
    total=0;receipts=[]
    for row in range(24):
        expected=factor_receipt(grammar,row,state)
        need(canonical(claimed[row])==canonical(expected),'complete literal factor stream row '+str(row))
        receipts.append(expected);total+=expected['count']
    return dict(complete_initial_candidate_count=total,rows=24,
        all_required_rows_checked=True,complete_point_factor_streams=receipts,
        candidate_set_authority='every zero-port key or ordered Cartesian MP reference key represented by independently regenerated literal t/m factors',
        target_searches=0,proof_certificates=0,native_accepted=False,resource_accepted=False)


def seed_placements(grammar, recipe_ids):
    """Independently reproduce all three full original decorated identities."""
    answer=[]
    for row,index in enumerate(grammar.assumptions):
        recipe,_,code,inputs=grammar.recipe(index,logical_check=False)
        need(not inputs and recipe_ids[index]==recipe['id'],'original zero-port occurrence seed')
        witness=recipe['primitive_witness'];t=[[0,row,1]];m=[[1,row,code]]
        prototype=dict(recipe_id=recipe['id'],primitive_witness=witness,
            ordered_premise_formulas=[],relative_ordered_input_offsets=[],orientation='identity',
            t=[[0,0,1]],m=[[1,0,code]],marking_version=MARKING,
            formula_registry_sha256=grammar.registry_sha,authority_epoch=grammar.authority['epoch'])
        preimage=dict(prototype_id='primitive-prototype-'+digest(prototype),
            prototype_preimage=prototype,transform=[0,row],context_id=grammar.context_id,
            ordered_input_rows=[],primitive_command=witness,t=t,m=m,
            authority_epoch=grammar.authority['epoch'],formula_registry_sha256=grammar.registry_sha)
        answer.append(dict(id='aggregate-primitive-'+digest(preimage),identity_preimage=preimage,
                           key=[index,row,[]],command=witness,t=t,m=m))
    return answer
