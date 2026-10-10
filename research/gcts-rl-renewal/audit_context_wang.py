"""Derive all native nodes again and bind each inference to the exact request."""
import copy,gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
from audit_logical_wang_clusters import artifact,checked_chain
from audit_proof_boundary import PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE,expected_constructor,code_bytes,input_bytes,micro_output
from audit_tree_kernel import need,packed
from check_compact_contexts import certificate
from audit_serialized_kernel import replay

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-context-wang-audit-001')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);path=DOC/'context-wang-001.json.gz'
    data=json.loads(gzip.decompress(path.read_bytes()));source=json.loads((DOC/'compact-contexts-001.json').read_bytes())
    need((data['program_sha256'],data['micro_sha256'],data['literal_table_sha256'])==(PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE),'fixed program pins')
    need(data['inventory_fingerprint']=='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455','same literal palette')
    for field,root in (('sources',HERE),('reused_source_pins',HERE),('reused_artifacts',DOC)):
        for n,pin in data[field].items():need(digest(root/n)==pin,'unchanged source/artifact '+n)
    donor=next(c for c in source['cases'] if c['spec']['id']=='branch-donor');certificate(donor['spec'],donor['result'])
    micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()))
    need(hashlib.sha256(packed(micro)).hexdigest()==PINNED_MICRO,'micro hash')
    (TMP/'code.bin').write_bytes(code_bytes(micro));subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'micro_line_check.cpp'),'-o',str(TMP/'checker')],check=True)
    checks=[];mutations=[]
    for row in data['cases']:
        start=time.perf_counter();request=copy.deepcopy(donor['result']['compact']['request'])
        if row['name']=='invalid-projection':request['proof'][0]['formula']=['imp',donor['result']['compact']['context'],['bot']]
        else:need(row['name']=='branched-theorem','declared native experiment')
        need(row['request']==request,'entire searched-source request or declared mutation')
        need(replay(packed(request))['status']==row['expected']['status'],'separate complete logical kernel')
        expected_constructor(micro,row['initial'],request)
        raw=artifact(row['grammar']);events=[json.loads(s) for s in artifact(row['events']).splitlines()];stored=json.loads(artifact(row['responses']))
        (TMP/'grammar.bin').write_bytes(raw);(TMP/'input.bin').write_bytes(input_bytes(row['initial']));need(digest(TMP/'input.bin')==row['input_sha256'],'native input hash')
        ids=[e['node'] for e in events if e['kind']=='fragment'];(TMP/'observed.bin').write_bytes(struct.pack('<'+'I'*(len(ids)+1),len(ids),*ids))
        checked=json.loads(subprocess.check_output([str(TMP/'checker'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'grammar.bin'),str(TMP/'output.bin'),str(10**10),str(1500000000),str(TMP/'root.json'),str(TMP/'observed.bin')]))
        need(checked['status']=='checked_response' and checked['result']==row['expected']['status'] and digest(TMP/'output.bin')==row['output_sha256'],'fresh whole native derivation')
        root=json.loads((TMP/'root.json').read_text());need(root==stored,'all stored response claims')
        chain=checked_chain(row,micro,events,root);need(chain.pop('final')==micro_output(TMP/'output.bin')==row['output'],'complete applied fragments and final bands')
        for k in ('status','micro_steps','physical_steps'):need(row['literal'][k]==row['builder'][k]==row['expected'][k],'literal and selected execution agreement')
        for name in ('input-target','context-theory','register','heap','input-head','output-state','node','cost'):
            bad=copy.deepcopy(row);es=copy.deepcopy(events);rs=copy.deepcopy(root)
            cp=next(e for e in es if e['kind']=='checkpoint');f=next(e for e in es if e['kind']=='fragment')
            if name=='input-target':bad['request']['target']=['bot']
            elif name=='context-theory':bad['request']['theory']['axioms']['injected']=['bot']
            elif name=='register':cp['register_words'][0]='0'
            elif name=='heap':cp['heap']=cp['heap'][:-1]
            elif name=='input-head':f['input_head']+=1
            elif name=='output-state':f['out']+=1
            elif name=='node':f['node']=0xffffffff
            else:
                response=next(v['response'] for v in rs['observations'] if v['node']==f['node']);response['physical_constant']=str(int(response['physical_constant'])+1)
            try:expected_constructor(micro,bad['initial'],bad['request']);checked_chain(bad,micro,es,rs)
            except (ValueError,KeyError,IndexError):mutations.append(dict(case=row['name'],kind=name))
            else:raise ValueError('native mutation accepted '+name)
        checks.append(dict(name=row['name'],result=checked['result'],checker=checked,independent_seconds=time.perf_counter()-start,**chain))
        print(row['name'],len(chain['lines']),'inferences and all operational nodes independently checked',flush=True)
    out=dict(version='context-wang-audit-001',status='passed',input_sha256=digest(path),source_sha256=digest(__file__),
        helpers={n:digest(HERE/n) for n in ('check_compact_contexts.py','audit_logical_wang_clusters.py','audit_proof_boundary.py','micro_line_check.cpp')},
        cases=checks,mutations_rejected=mutations,seconds=time.perf_counter()-began,
        scope='Fresh derivation of every native grammar node, actual per-inference heap/register contexts and full output; unchanged literal lowering law. '
              'Root assumptions, checked inventory and forbidden variables are empty; original theory remains unchanged. Finite evidence only.')
    (DOC/'context-wang-audit-001.json.gz').write_bytes(gzip.compress(packed(out)+b'\n',mtime=0));print('native audit complete',out['seconds'],flush=True)
if __name__=='__main__':main()
