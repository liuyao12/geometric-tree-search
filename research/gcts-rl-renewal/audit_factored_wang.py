"""Fresh full response derivation and exact conditional-source/context binding."""
import copy,gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
from audit_propositional_wang import bind_compilation
from audit_logical_wang_clusters import checked_chain,artifact
from audit_proof_boundary import expected_constructor,code_bytes,input_bytes,micro_output,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from audit_tree_kernel import need,packed
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-factored-wang-audit-001')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);path=DOC/'factored-wang-001.json.gz';data=json.loads(gzip.decompress(path.read_bytes()))
    need((data['program_sha256'],data['micro_sha256'],data['literal_table_sha256'])==(PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE),'fixed code')
    need(data['inventory_fingerprint']=='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455','fixed inventory')
    for n,p in data['sources'].items():need(digest(HERE/n)==p,'source '+n)
    need(data['search_sha256']==digest(DOC/'factored-receptors-001.json'),'actual search source')
    search=json.loads((DOC/'factored-receptors-001.json').read_text());case=next(c for c in search['cases'] if c['id']=='double-negation-premise');row=data['cases'][0]
    need(len(data['cases'])==1 and row['source']==dict(proof=case['runs']['factored']['proof'],target=case['target'],hypotheses=case['hypotheses'],atoms=None,signature=None),'exact new proof/hypothesis provenance')
    bind_compilation(row);micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()));need(hashlib.sha256(packed(micro)).hexdigest()==PINNED_MICRO,'micro content')
    expected_constructor(micro,row['initial'],row['request']);original=json.loads((DOC/'proof-boundary-001.json').read_text())['cases'][0]['initial'];bootstrap=copy.deepcopy(row['initial'])
    for band in (micro['boundary']['problem'],micro['boundary']['certificate']):
        need(bootstrap['capacities'][band]==len(bootstrap['words'][band])+2,'input frame');bootstrap['capacities'][band]=original['capacities'][band];bootstrap['words'][band]=original['words'][band]
    need(bootstrap==original,'unchanged bootstrap')
    (TMP/'code.bin').write_bytes(code_bytes(micro));(TMP/'input.bin').write_bytes(input_bytes(row['initial']));need(digest(TMP/'input.bin')==row['input_sha256'],'input pin')
    (TMP/'grammar.bin').write_bytes(artifact(row['grammar']));events=[json.loads(s) for s in artifact(row['events']).splitlines()];ids=[e['node'] for e in events if e['kind']=='fragment']
    (TMP/'observed.bin').write_bytes(struct.pack('<'+'I'*(len(ids)+1),len(ids),*ids));subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'micro_line_check.cpp'),'-o',str(TMP/'checker')],check=True)
    r=json.loads(subprocess.check_output([str(TMP/'checker'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'grammar.bin'),str(TMP/'output.bin'),str(10**10),str(1500000000),str(TMP/'root.json'),str(TMP/'observed.bin')]))
    need(r['status']=='checked_response' and r['result']=='accepted' and digest(TMP/'output.bin')==row['output_sha256'],'complete independently derived response')
    responses=json.loads((TMP/'root.json').read_text());need(responses==json.loads(artifact(row['responses'])),'all line responses');chain=checked_chain(row,micro,events,responses)
    for k in ('status','micro_steps','physical_steps'):need(row['literal'][k]==row['builder'][k]==row['expected'][k],'actual literal result and complete counts')
    need(chain.pop('final')==micro_output(TMP/'output.bin')==row['output'],'all final registers');need(len(chain['lines'])==5,'one premise axiom plus four new inference commands')
    for kind in ('premise','target','ref-shift'):
        bad=copy.deepcopy(row)
        if kind=='premise':bad['request']['theory']['axioms']['premise-0']=['bot']
        elif kind=='target':bad['request']['target']=['bot']
        else:bad['request']['proof'][2]['antecedent']+=1
        try:bind_compilation(bad);expected_constructor(micro,bad['initial'],bad['request'])
        except ValueError:pass
        else:raise ValueError('changed input accepted '+kind)
    out=dict(version='factored-wang-audit-001',input_sha256=digest(path),source_sha256=digest(__file__),helper_sources={n:digest(HERE/n) for n in ('audit_propositional_wang.py','audit_logical_wang_clusters.py','audit_proof_boundary.py','micro_line_check.cpp')},cases=[chain],checker=r,mutations_rejected=3,seconds=time.perf_counter()-began,
        scope='Every native grammar node derived afresh, full source/premise/reference and input binding, five actual inference contexts; unchanged earlier literal lowering law reused.')
    (DOC/'factored-wang-audit-001.json.gz').write_bytes(gzip.compress(packed(out)+b'\n',mtime=0));print('native audit complete',out['seconds'],flush=True)
if __name__=='__main__':main()
