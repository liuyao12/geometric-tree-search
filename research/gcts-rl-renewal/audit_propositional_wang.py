"""Independent source, syntax, operational fragment and input binding audit.

Does not import the new compiler, producer or search engine. Reuses the
independent point checker and previously audited fixed literal lowering law.
"""
import copy,gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
import check_propositional_receptors as A
from audit_propositional_receptors import audit_case
from audit_semantic_proofs import whole_replay
from audit_logical_wang_clusters import artifact,checked_chain
from audit_proof_boundary import (PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE,
    expected_constructor,code_bytes,input_bytes,micro_output)
from audit_tree_kernel import need,packed

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-propositional-wang-audit-001')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha(a):return hashlib.sha256(packed(a)).hexdigest()
def uncompressed(name):return json.loads(gzip.decompress((DOC/name).read_bytes()))
def expected_compilation(spec):
    proof=A.frozen(spec['proof']);A.logical(proof,A.frozen(spec['target']),A.frozen(spec['hypotheses']))
    atoms=spec['atoms'] or {'P':['pred','P',[]],'Q':['pred','Q',[]]}
    signature=spec['signature'] or dict(functions={},predicates=dict(P=0,Q=0))
    def convert(a):
        if len(a)==1:return copy.deepcopy(atoms[a[0]])
        return [a[0]]+[convert(b) for b in a[1:]]
    blocks={};bindings=[]
    def translate(rows,hyp=(),root=False):
        commands=[];refs={}
        for n,f in enumerate(hyp,-len(hyp)):
            refs[n]=len(commands);commands.append(dict(rule='axiom' if root else 'assumption',formula=convert(f),
                **({'name':'premise-'+str(n+len(hyp))} if root else {'index':n+len(hyp)})))
        for n,line in enumerate(rows):
            f=convert(line['formula']);kind=line['kind']
            if kind in ('H1','H2','H3'):cmd=dict(rule='tautology',formula=f)
            elif kind=='mp':cmd=dict(rule='mp',formula=f,antecedent=refs[line['refs'][0]],implication=refs[line['refs'][1]])
            elif kind=='lemma':
                body=translate(line['expansion']);block=dict(premises=[],conclusion=f,proof=body)
                name='identity-'+sha(block)[:20]
                need(name not in blocks or blocks[name]==block,'exact block declaration on name collision')
                blocks[name]=block;cmd=dict(rule='block',formula=f,name=name,inputs=[])
            else:raise ValueError('source rule')
            refs[n]=len(commands);commands.append(cmd)
            if root:bindings.append(dict(source_slot=n,compiled_line=refs[n],source_kind=kind,formula=f,
                definition=cmd.get('name') if kind=='lemma' else None))
        return commands
    commands=translate(proof,A.frozen(spec['hypotheses']),True)
    request=dict(protocol='gcts-fol-1',theory=dict(signature,axioms={'premise-'+str(j):convert(f) for j,f in enumerate(spec['hypotheses'])},schemas=[]),
        target=convert(spec['target']),blocks=[dict(name=n,**b) for n,b in blocks.items()],proof=commands)
    return request,bindings
def bind_compilation(row):
    request,bindings=expected_compilation(row['source']);c=row['compiler']
    need(c['request']==request and c['bindings']==bindings,'independent syntax and binding translation')
    need(c['logical_commands']==len(row['source']['proof']) and c['primitive_lines']==A.logical(A.frozen(row['source']['proof']),A.frozen(row['source']['target']),A.frozen(row['source']['hypotheses']))['primitive_lines'],'source expansion costs')
    need(c['certificate_pin']==sha(request) and c['statement_pin']==sha({k:request[k] for k in ('protocol','theory','target')}),'compiled pins')
    actual=copy.deepcopy(request)
    if row['name']=='invalid-unused-definition':actual['blocks'][0]['proof'][0]['formula']=['pred','P',[]]
    elif row['name']=='wrong-fixed-target':actual['target']=['bot']
    need(actual==row['request'],'exact request or declared single mutation')
    try:status=whole_replay(actual)['status']
    except ValueError:status='rejected'
    need(status==row['expected']['status'],'independent structured logical checker')
    need(sha({k:actual[k] for k in ('protocol','theory','target')})==row['problem_pin'],'fixed statement binding')
    return request
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);path=DOC/'propositional-wang-001.json.gz';data=uncompressed(path.name)
    need((data['program_sha256'],data['micro_sha256'],data['literal_table_sha256'])==(PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE),'fixed machines')
    need(data['inventory_fingerprint']=='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455','unchanged palette')
    for field,root in (('sources',HERE),('reused_source_pins',HERE),('reused_artifacts',DOC)):
        for n,pin in data[field].items():need(digest(root/n)==pin,'source/artifact '+n)
    prior=A.frozen(json.loads((DOC/'propositional-receptors-001.json').read_text()))
    need(prior['discovered_family']['proof']==prior['donor']['proof'],'actual promoted identity family')
    p,q=('P',),('Q',);imp=lambda a,b:('imp',a,b)
    searches=[]
    for lane,s in data['searches'].items():
        target=imp(p,p) if lane=='template' else imp(q,imp(p,p));length=1 if lane=='template' else 3
        need(A.frozen(s['target'])==target and s['length']==length,'independent fresh task registry')
        result=A.frozen(s['result']);result['primitive_lines']=A.logical(result['proof'],target)['primitive_lines']
        case=dict(id=lane,target=target,length=length,hypotheses=(),library=True,runs={lane if lane!='template' else 'point':result})
        audit_case(prior,case);searches.append(dict(lane=lane,nodes=s['result']['metrics']['nodes'],status='complete_tree_and_points_replayed'))
    compound=next(c for c in prior['cases'] if c['id']=='family-composite')
    for row in data['cases']+data['controls']:
        s=A.frozen(row['source']);name=row['name']
        if name in ('fresh-hierarchy','invalid-unused-definition','wrong-fixed-target'):
            need(s['proof']==A.frozen(data['searches']['point-rl']['result']['proof']) and s['target']==imp(q,imp(p,p)),'fresh discovery provenance')
        elif name=='primitive-identity':need(s['proof']==prior['donor']['proof'] and s['target']==imp(p,p),'donor provenance')
        elif name=='compound-family':need(s['proof']==compound['runs']['point']['proof'] and s['target']==compound['target'],'compound source provenance')
        else:
            need(name in ('arithmetic-syntax-family','geometry-syntax-family') and s['proof']==A.frozen(data['searches']['template']['result']['proof']) and s['target']==imp(p,p),'symbolic template provenance')
            x=['var','x'];u=['var','u']
            atom=['all','x',['eq',['fun','add',[x,['fun','zero',[]]]],x]] if name.startswith('arithmetic') else ['all','x',['all','u',['imp',['pred','Inc',[x,u]],['pred','Point',[x]]]]]
            sig=dict(functions=dict(zero=0,add=2),predicates={}) if name.startswith('arithmetic') else dict(functions={},predicates=dict(Inc=2,Point=1))
            need(row['source']['atoms']=={'P':atom} and row['source']['signature']==sig,'independent symbolic embedding')
        need(not row['source']['hypotheses'],'external closed tasks')
        if name not in ('arithmetic-syntax-family','geometry-syntax-family'):need(row['source']['atoms'] is None and row['source']['signature'] is None,'default symbolic language')
    micro=uncompressed('proof-boundary-microcode-001.json.gz');need(sha(micro)==PINNED_MICRO,'micro program')
    (TMP/'code.bin').write_bytes(code_bytes(micro));subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'micro_line_check.cpp'),'-o',str(TMP/'checker')],check=True)
    results=[];mutations=[];rules=set()
    for row in data['cases']+data['controls']:
        start=time.perf_counter();bind_compilation(row);expected_constructor(micro,row['initial'],row['request'])
        raw=artifact(row['grammar']);events=[json.loads(s) for s in artifact(row['events']).splitlines()];stored=json.loads(artifact(row['responses']))
        (TMP/'grammar.bin').write_bytes(raw);(TMP/'input.bin').write_bytes(input_bytes(row['initial']));need(digest(TMP/'input.bin')==row['input_sha256'],'input pin')
        ids=[e['node'] for e in events if e['kind']=='fragment'];(TMP/'observed.bin').write_bytes(struct.pack('<'+'I'*(len(ids)+1),len(ids),*ids))
        r=json.loads(subprocess.check_output([str(TMP/'checker'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'grammar.bin'),str(TMP/'output.bin'),str(10**10),str(1500000000),str(TMP/'root.json'),str(TMP/'observed.bin')]))
        need(r['status']=='checked_response' and r['result']==row['expected']['status'] and digest(TMP/'output.bin')==row['output_sha256'],'fresh native whole response')
        root=json.loads((TMP/'root.json').read_text());need(root==stored,'all derived responses')
        chain=checked_chain(row,micro,events,root);need(chain.pop('final')==micro_output(TMP/'output.bin')==row['output'],'complete final output')
        for line in chain['lines']:
            if line['outcome']=='line-checked':rules.add(line['label']['rule'])
        for k in ('status','micro_steps','physical_steps'):need(row['literal'][k]==row['builder'][k]==row['expected'][k],'literal execution and selected execution')
        for kind in ('source-kind','binding-line','compiled-signature','checkpoint-register','checkpoint-heap','incoming-head','outgoing-state','fragment-node','fragment-cost','fixed-target'):
            bad=copy.deepcopy(row);es=copy.deepcopy(events);rs=copy.deepcopy(root)
            cp=next(e for e in es if e['kind']=='checkpoint');f=next(e for e in es if e['kind']=='fragment')
            if kind=='source-kind':bad['source']['proof'][0]['kind']='mp';bad['source']['proof'][0]['refs']=[0,0]
            elif kind=='binding-line':bad['compiler']['bindings'][0]['compiled_line']+=1
            elif kind=='compiled-signature':bad['compiler']['request']['theory']['predicates']['unexpected']=0
            elif kind=='checkpoint-register':cp['register_words'][0]='0'
            elif kind=='checkpoint-heap':cp['heap']=cp['heap'][:-1]
            elif kind=='incoming-head':f['input_head']+=1
            elif kind=='outgoing-state':f['out']+=1
            elif kind=='fragment-node':f['node']=0xffffffff
            elif kind=='fragment-cost':
                resp=next(o['response'] for o in rs['observations'] if o['node']==f['node']);resp['physical_constant']=str(int(resp['physical_constant'])+1)
            else:bad['request']['target']=['pred','Changed',[]]
            try:bind_compilation(bad);expected_constructor(micro,bad['initial'],bad['request']);checked_chain(bad,micro,es,rs)
            except (ValueError,KeyError,IndexError,AssertionError):mutations.append(dict(case=row['name'],kind=kind))
            else:raise ValueError('mutation accepted '+row['name']+' '+kind)
        results.append(dict(name=row['name'],result=r['result'],checker=r,independent_seconds=time.perf_counter()-start,**chain))
        print(row['name'],len(chain['lines']),'lines bound',flush=True)
    out=dict(version='propositional-wang-audit-001',input_sha256=digest(path),source_sha256=digest(__file__),
        helper_sources={n:digest(HERE/n) for n in ('check_propositional_receptors.py','audit_propositional_receptors.py','audit_semantic_proofs.py','audit_logical_wang_clusters.py','audit_proof_boundary.py','audit_tree_kernel.py','micro_line_check.cpp')},
        searches=searches,cases=results,checked_rules=sorted(rules),mutations_rejected=mutations,seconds=time.perf_counter()-began,
        scope='Complete fresh point-tree replay; independent syntax/source mapping; all native grammar nodes derived again and observed fragments bound to decoded contexts. Reuses unchanged literal lowering law. No universal compiler proof or literal-tile GCTS search.')
    (DOC/'propositional-wang-audit-001.json.gz').write_bytes(gzip.compress(packed(out)+b'\n',mtime=0));print('audit complete',out['seconds'],flush=True)
if __name__=='__main__':main()
