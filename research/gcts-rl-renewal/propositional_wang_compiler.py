"""Generic syntax bridge from checked receptor proofs to the frozen FOL core.

Parameters change encoded input and concrete block definitions, never the
machine or literal palette. This is a compiler, not literal-tile proof search.
"""
import copy,hashlib
import check_propositional_receptors as A
from serialized_kernel import canonical,check,problem_hash,PROTOCOL

DEFAULT_ATOMS={'P':['pred','P',[]],'Q':['pred','Q',[]]}
DEFAULT_SIGNATURE=dict(functions={},predicates=dict(P=0,Q=0))

def lift(a,atoms):
    if len(a)==1:return copy.deepcopy(atoms[a[0]])
    return [a[0],*[lift(v,atoms) for v in a[1:]]]

def compile_request(proof,target,hypotheses=(),atoms=None,signature=None):
    proof=A.frozen(proof);target=A.frozen(target);hypotheses=A.frozen(hypotheses)
    A.logical(proof,target,hypotheses)
    atoms=copy.deepcopy(DEFAULT_ATOMS if atoms is None else atoms)
    signature=copy.deepcopy(DEFAULT_SIGNATURE if signature is None else signature)
    if set(signature)!=set(('functions','predicates')):raise ValueError('only an explicit signature is accepted')
    definitions={};bindings=[]
    def commands(rows,premises=(),root=False):
        out=[];references={}
        for j,a in enumerate(premises,-len(premises)):
            references[j]=len(out);out.append(dict(rule='axiom' if root else 'assumption',formula=lift(a,atoms),
                **({'name':'premise-'+str(j+len(premises))} if root else {'index':j+len(premises)})))
        for j,row in enumerate(rows):
            a=lift(row['formula'],atoms);kind=row['kind']
            if kind in ('H1','H2','H3'):command=dict(rule='tautology',formula=a)
            elif kind=='mp':command=dict(rule='mp',formula=a,antecedent=references[row['refs'][0]],implication=references[row['refs'][1]])
            elif kind=='lemma':
                body=commands(row['expansion']);declaration=dict(premises=[],conclusion=a,proof=body)
                name='identity-'+hashlib.sha256(canonical(declaration)).hexdigest()[:20]
                if name in definitions and definitions[name]!=declaration:raise ValueError('definition-name collision')
                definitions[name]=declaration;command=dict(rule='block',formula=a,name=name,inputs=[])
            else:raise ValueError('unavailable source inference')
            references[j]=len(out);out.append(command)
            if root:bindings.append(dict(source_slot=j,compiled_line=references[j],source_kind=kind,
                formula=a,definition=command.get('name') if kind=='lemma' else None))
        return out
    rows=commands(proof,hypotheses,True)
    theory=dict(signature,axioms={'premise-'+str(j):lift(a,atoms) for j,a in enumerate(hypotheses)},schemas=[])
    request=dict(protocol=PROTOCOL,theory=theory,target=lift(target,atoms),
                 blocks=[dict(name=name,**declaration) for name,declaration in definitions.items()],proof=rows)
    raw=canonical(request);checked=check(raw,expected_problem_sha256=problem_hash(request))
    if checked['status']!='accepted':raise ValueError(('compiled request rejected',checked))
    return dict(request=request,bindings=bindings,atoms=atoms,signature=signature,host=checked,
        logical_commands=len(proof),primitive_lines=A.logical(proof,target,hypotheses)['primitive_lines'],
        statement_pin=problem_hash(request),certificate_pin=hashlib.sha256(raw).hexdigest(),
        scope='Source H schemas lower to checked tautology commands; hypotheses become exactly the declared closed premise axioms; concrete family definitions are checked by the unchanged core.')

def embedding(kind):
    if kind=='arithmetic':
        x=['var','x'];z=['fun','zero',[]]
        atom=['all','x',['eq',['fun','add',[x,z]],x]]
        signature=dict(functions=dict(zero=0,add=2),predicates={})
    elif kind=='geometry':
        x=['var','x'];u=['var','u']
        atom=['all','x',['all','u',['imp',['pred','Inc',[x,u]],['pred','Point',[x]]]]]
        signature=dict(functions={},predicates=dict(Inc=2,Point=1))
    else:raise ValueError('embedding kind')
    return dict(atoms={'P':atom},signature=signature)

def term_tex(t):
    if t[0]=='var':return t[1]
    if t[1]=='zero' and not t[2]:return '0'
    if t[1]=='add':return '('+term_tex(t[2][0])+'+'+term_tex(t[2][1])+')'
    return r'\operatorname{'+t[1]+'}('+','.join(term_tex(a) for a in t[2])+')'
def formula_tex(a):
    k=a[0]
    if k=='pred':return r'\operatorname{'+a[1]+'}'+('('+','.join(term_tex(t) for t in a[2])+')' if a[2] else '')
    if k=='eq':return '('+term_tex(a[1])+'='+term_tex(a[2])+')'
    if k=='all':return r'\forall '+a[1]+r'\,('+formula_tex(a[2])+')'
    if k=='not':return r'\neg ('+formula_tex(a[1])+')'
    if k=='imp':return '('+formula_tex(a[1])+r'\Rightarrow '+formula_tex(a[2])+')'
    if k=='bot':return r'\bot'
    raise ValueError('display grammar')
