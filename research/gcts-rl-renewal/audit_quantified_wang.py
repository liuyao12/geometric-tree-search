"""Full operational derivation of the newly discovered quantified requests."""
import copy,gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
from audit_quantified_receptors import bind_compiled
from audit_logical_wang_clusters import checked_chain,artifact
from audit_proof_boundary import expected_constructor,code_bytes,input_bytes,micro_output,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from audit_tree_kernel import need,packed
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-quantified-wang-audit-001')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    start=time.perf_counter();TMP.mkdir(exist_ok=True);path=DOC/'quantified-wang-001.json.gz';data=json.loads(gzip.decompress(path.read_bytes()));search=json.loads((DOC/'quantified-receptors-001.json').read_bytes())
    need(data['search_sha256']==digest(DOC/'quantified-receptors-001.json'),'discovered source pin');need((data['program_sha256'],data['micro_sha256'],data['literal_table_sha256'])==(PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE),'fixed code');need(data['inventory_fingerprint']=='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455','fixed palette')
    for n,p in data['sources'].items():need(digest(HERE/n)==p,'measured native source '+n)
    need([r['name'] for r in data['cases']]==['arithmetic','hilbert-typing','ambient-y','arithmetic-learned-6'],'exact native cases')
    micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()));need(hashlib.sha256(packed(micro)).hexdigest()==PINNED_MICRO,'micro contents');(TMP/'code.bin').write_bytes(code_bytes(micro))
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'micro_line_check.cpp'),'-o',str(TMP/'checker')],check=True);reports=[];mutations=[]
    original=json.loads((DOC/'proof-boundary-001.json').read_bytes())['cases'][0]['initial']
    for row in data['cases']:
        case=next(c for c in search['cases'] if c['spec']['id']==row['name']);source=case['runs']['gcts']
        need(row['spec']==case['spec'] and row['source']==source['proof'] and row['compiler']==source['compiled'] and row['request']==source['compiled']['request'],'actual search and whole compiler binding');bind_compiled(case['spec'],source)
        expected_constructor(micro,row['initial'],row['request']);bootstrap=copy.deepcopy(row['initial'])
        for band in (micro['boundary']['problem'],micro['boundary']['certificate']):
            need(bootstrap['capacities'][band]==len(bootstrap['words'][band])+2,'wire frame');bootstrap['capacities'][band]=original['capacities'][band];bootstrap['words'][band]=original['words'][band]
        need(bootstrap==original,'unchanged bootstrap');folder=TMP/row['name'];folder.mkdir(exist_ok=True);(folder/'input.bin').write_bytes(input_bytes(row['initial']));need(digest(folder/'input.bin')==row['input_sha256'],'input bytes')
        (folder/'grammar.bin').write_bytes(artifact(row['grammar']));events=[json.loads(s) for s in artifact(row['events']).splitlines()];ids=[e['node'] for e in events if e['kind']=='fragment'];(folder/'observed.bin').write_bytes(struct.pack('<'+'I'*(len(ids)+1),len(ids),*ids))
        r=json.loads(subprocess.check_output([str(TMP/'checker'),str(TMP/'code.bin'),str(folder/'input.bin'),str(folder/'grammar.bin'),str(folder/'output.bin'),str(10**10),str(1500000000),str(folder/'root.json'),str(folder/'observed.bin')]))
        need(r['status']=='checked_response' and r['result']=='accepted' and digest(folder/'output.bin')==row['output_sha256'],'every native node derived afresh');responses=json.loads((folder/'root.json').read_bytes());need(responses==json.loads(artifact(row['responses'])),'all operational responses');chain=checked_chain(row,micro,events,responses)
        need(chain.pop('final')==micro_output(folder/'output.bin')==row['output'],'all final registers')
        for k in ('status','micro_steps','physical_steps'):need(row['literal'][k]==row['builder'][k]==row['expected'][k],'actual literal count '+k)
        need(len(chain['lines'])==sum(len(b['proof']) for b in row['request']['blocks'])+len(row['request']['proof']),'all inference fragments')
        if row['name']=='ambient-y':
            body=[l for l in chain['lines'] if l['label']['scope']=='discovered-sequent'];need(body and all(l['input_context']['forbidden']==['y'] for l in body),'actual open y scope');need(any(l['label']['rule']=='generalize' for l in body),'actual permitted generalization')
        for kind in ('target','theory','reference'):
            bad=copy.deepcopy(row['request'])
            if kind=='target':bad['target']=['bot']
            elif kind=='theory':bad['theory']['schemas']=['nat-induction']
            else:
                lines=bad['blocks'][0]['proof'] if bad['blocks'] else bad['proof'];line=next(l for l in lines if l['rule']=='mp');line['antecedent']+=1
            try:expected_constructor(micro,row['initial'],bad)
            except ValueError:mutations.append(dict(case=row['name'],kind=kind))
            else:raise ValueError('changed input accepted '+kind)
        reports.append(dict(name=row['name'],checker=r,**chain));print(row['name'],'operationally audited',flush=True)
    out=dict(version='quantified-wang-audit-001',input_sha256=digest(path),source_sha256=digest(__file__),helper_sources={n:digest(HERE/n) for n in ('audit_quantified_receptors.py','check_quantified_receptors.py','audit_logical_wang_clusters.py','audit_proof_boundary.py','micro_line_check.cpp')},cases=reports,mutations_rejected=mutations,seconds=time.perf_counter()-start,
        scope='All native nodes derived anew and full theory/target/assumption/forbidden/prior/pending context decoded; actual literal counts and all bands match; exact closed root and open sequent declaration meanings remain distinct. Earlier exhaustive literal lowering laws reused.')
    (DOC/'quantified-wang-audit-001.json.gz').write_bytes(gzip.compress(packed(out)+b'\n',mtime=0));print('native audit complete',out['seconds'],flush=True)
if __name__=='__main__':main()
