"""New derived-premise boundaries; no target proof sequence is supplied."""
import copy,json
from hilbert_receptors_catalog import F,P,I,condition,axiom,syntax_and_definitions

def recipients():
    p,q,r,l,m=map(F,['P','Q','R','l','m']);ready=P('Point',r)
    signature=dict(functions={x:0 for x in ['P','Q','R','l','m']},predicates=dict(Point=1,Line=1,Incident=2),schemas=[])
    output=[]
    for group,left,right,short,enough in [('delayed-common',l,m,5,6),('coupled-reverse',m,l,6,7)]:
        h=condition(p,q,left,right);inc=P('Incident',r,left)
        hypotheses={'readiness':ready,'common-from-readiness':I(ready,h)}
        hypotheses['extra-incidence' if group=='delayed-common' else 'incidence-from-common']=inc if group=='delayed-common' else I(h,inc)
        theory=dict(**copy.deepcopy(signature),axioms={'I.2-uniqueness':axiom(),**hypotheses})
        for boundary,length in [('short',short),('sufficient',enough)]:
            output.append(dict(id='transfer-'+group+'-'+boundary,group=group,boundary=boundary,length=length,
                title=group+' derived-premise incidence: '+str(length)+' rows',theory=copy.deepcopy(theory),
                sorts={'point':['P','Q','R'],'line':['l','m']},uniqueness_points=['P','Q'],target=P('Incident',r,right),
                receptor_common=h,receptor_incidence=inc,required_derivation='common input is derived by MP' if group=='delayed-common' else 'both inputs are derived in sequence; reversed line receptor',
                scope='Unchanged symbolic signature and admitted receptors; changed closed hypothesis dependencies, no supplied target proof or pure-renaming difficulty claim.'))
    return output
def build(specs,prior_catalog):
    groups={}
    for spec in specs:
        built=syntax_and_definitions(spec)
        if json.dumps(built['definitions'],sort_keys=True,separators=(',',':'))!=json.dumps(prior_catalog['base_definitions'],sort_keys=True,separators=(',',':')):raise ValueError('all unchanged 28 target-independent interfaces')
        if spec['group'] not in groups:groups[spec['group']]=dict(basis=built['catalog']['basis'],catalog=built['catalog'],representative=spec)
    return dict(cases=specs,groups=groups,base_definitions=prior_catalog['base_definitions'],promoted_definitions=prior_catalog['promoted_definitions'],
        binding_records=prior_catalog['binding_records'],definitions=prior_catalog['definitions'],bindings=48,inventory_change=False)
