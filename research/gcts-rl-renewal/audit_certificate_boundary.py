"""Independent finite grammar, chronological trees and all native computations.

No search, producer, case registry or boundary encoder import. Reconstructs
payload words independently; a separately written interpreter replays every
recorded accepted, rejected and unfinished query from its actual program start.
"""
import copy,gzip,hashlib,itertools,json,math,struct,subprocess,time
from pathlib import Path
from audit_tree_kernel import need,packed
from audit_proof_boundary import code_bytes,input_bytes,expected_constructor,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from audit_semantic_proofs import whole_replay
from audit_logical_wang_clusters import checked_chain
from micro_cert import write_cuts,run
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-certificate-boundary-audit-001')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(v):return hashlib.sha256(packed(v)).hexdigest()
def load(n):return json.loads(gzip.decompress((DOCS/n).read_bytes()))
def artifact(a):
    p=DOCS/a['name'];need(sha(p)==a['sha256'] and p.stat().st_size==a['bytes'],'artifact binding '+a['name']);b=gzip.decompress(p.read_bytes());need(len(b)==a['uncompressed_bytes'],'artifact length');return b
def grammar(spec):
    formulas={};variables=set();pending=[spec['target'],*spec['theory']['axioms'].values()]
    def term(t):
        if t[0]=='var':variables.add(t[1])
        else:
            for s in t[2]:term(s)
    while pending:
        a=pending.pop();formulas[packed(a)]=a
        if a[0]=='all':variables.add(a[1]);pending.append(a[2])
        elif a[0] in ('imp','and','or'):pending.extend(a[1:])
        elif a[0]=='not':pending.append(a[1])
        elif a[0]=='eq':term(a[1]);term(a[2])
        elif a[0]=='pred':
            for t in a[2]:term(t)
    basis=[formulas[k] for k in sorted(formulas)];variables=sorted(variables);domains=[]
    for i in range(spec['length']):
        rows=[]
        for a in [spec['target']] if i+1==spec['length'] else basis:
            for n in sorted(spec['theory']['axioms']):rows.append(dict(rule='axiom',formula=a,name=n))
            for x in variables:
                for j in range(i):rows.append(dict(rule='generalize',formula=a,variable=x,source=j))
            for j in range(i):
                for k in range(i):rows.append(dict(rule='mp',formula=a,antecedent=j,implication=k))
            for rule in ('refl','tautology'):rows.append(dict(rule=rule,formula=a))
        domains.append(sorted(rows,key=lambda r:(r['rule'],packed(r['formula']),packed(r))))
    return basis,variables,domains
class Stopped(Exception):pass
def tree(r):
    spec=r['case'];basis,variables,domains=grammar(spec);g=r['grammar'];need(g['basis']==basis and g['variables']==variables and g['domains']==domains,'complete syntactic grammar');need(g['command_counts']==list(map(len,domains)) and g['complete_words']==math.prod(map(len,domains)),'complete word count')
    need(r['mode'] in ('prefix','flat') and r['root_path_restored'] is True,'control and root rollback');events=r['events'];records=r['records'];ei=qi=rejects=unknown=0;found=None;path=[];requests=[]
    def walk(i):
        nonlocal ei,qi,rejects,unknown,found
        for k,cmd in enumerate(domains[i]):
            if ei==len(events):raise Stopped()
            path.append(k)
            try:
                e=events[ei];ei+=1;final=i+1==len(domains);proof=[domains[j][c] for j,c in enumerate(path)];need((e['slot'],e['choice'],e['path'])==(i,k,path),'chronological complete alternatives')
                if r['mode']=='prefix' or final:
                    need(e['query']==qi and qi<len(records),'native query binding');rec=records[qi];request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=proof,target=spec['target'] if final else proof[-1]['formula']);requests.append(request)
                    need(rec['id']==qi and rec['request']==request and rec['request_sha256']==pin(request),'exact native request');need(rec['query_target']==('fixed_assertion' if final else 'prefix_final_formula'),'intermediate/final target role');qi+=1;status=rec['result']['status'];need(e['status']==status,'query result annotation')
                    if status=='rejected':need(e['action']=='reject','reject action');rejects+=not final;continue
                    if status!='accepted':need(status.startswith('unknown_') and e['action']=='unknown','unknown never prunes');unknown+=1;raise Stopped()
                    if final:
                        need(e['action']=='accept','accept action');found=dict(proof=proof,path=list(path),query=qi-1);return True
                else:need(e['query'] is None,'flat control has no prefix oracle')
                need(e['action']=='descend','accepted prefix descends')
                if walk(i+1):return True
            finally:path.pop()
        return False
    try:ok=walk(0);status='native_proof_discovered' if ok else 'exhausted_finite_certificate_grammar'
    except Stopped:
        status='unknown_search_budget';need(unknown or qi>=r['limits']['queries'] or r['seconds']>=r['limits']['seconds'],'justified unfinished tree')
    need(ei==len(events) and qi==len(records)==r['queries'] and ei==r['nodes'],'all tree events and queries');need(rejects==r['prefix_rejections'] and unknown==r['unknown_queries'],'all rejection/unknown counters');need(found==r['found'] and status==r['status'] and not path,'terminal/rollback binding');return requests
# Independent tagged JSON -> postfix tree words, without canonical heap IDs.
def value_word(v):
    atom=lambda n:'0'+''.join(str((n>>j)&1) for j in range(9))
    def word(xs):
        out=atom(256)
        for a in reversed(xs):out=a+out+'1'
        return out
    if type(v) is dict:tag=0;body=word([word([atom(c) for c in k.encode()])+value_word(x)+'1' for k,x in v.items()])
    elif type(v) is list:tag=1;body=word([value_word(x) for x in v])
    elif type(v) is str:tag=2;body=word([atom(c) for c in v.encode()])
    elif type(v) is bool:tag=5;body=atom(int(v))
    elif type(v) is int:tag=3 if v>=0 else 4;body=word([atom(1)]*abs(v))
    elif v is None:tag=6;body=atom(256)
    else:raise ValueError('exact JSON data')
    return atom(tag)+body+'1'
def initial_for(micro,template,request):
    initial=copy.deepcopy(template)
    for t,keys in ((micro['boundary']['problem'],('protocol','theory','target')),(micro['boundary']['certificate'],('blocks','proof'))):
        w=''.join(value_word(request[k]) for k in keys)+';:';initial['words'][t]=w;initial['heads'][t]=1;initial['capacities'][t]=len(w)+2
    expected_constructor(micro,initial,request);return initial

def mutations(r):
    attempts=[]
    def changed(name,edit):
        b=copy.deepcopy(r);edit(b)
        try:tree(b)
        except (ValueError,KeyError,IndexError):attempts.append(name)
        else:raise ValueError('corruption accepted '+name)
    changed('removed-original-command',lambda b:b['grammar']['domains'][0].pop())
    changed('skipped-tree-event',lambda b:b['events'].pop(0))
    changed('false-node-count',lambda b:b.update(nodes=b['nodes']+1))
    changed('changed-query-target',lambda b:b['records'][0]['request'].update(target=['bot']))
    changed('changed-target-role',lambda b:b['records'][0].update(query_target='prefix_final_formula' if b['records'][0]['query_target']=='fixed_assertion' else 'fixed_assertion'))
    changed('lost-rollback',lambda b:b.update(root_path_restored=False))
    changed('false-finite-exhaustion',lambda b:b.update(status='exhausted_finite_certificate_grammar'))
    changed('changed-chosen-proof',lambda b:b['found']['proof'][0].update(rule='tautology'))
    return attempts

def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);data=load('certificate-boundary-001.json.gz');need((data['program_sha256'],data['micro_sha256'],data['literal_table_sha256'])==(PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE),'fixed authority pins')
    for f,root in (('sources',HERE),('reused_sources',HERE),('reused_inputs',DOCS)):
        for n,p in data[f].items():need(sha(root/n)==p,'source/input binding '+n)
    micro=load('proof-boundary-microcode-001.json.gz');need(pin(micro)==PINNED_MICRO,'actual fixed code');template=json.loads((DOCS/'proof-boundary-001.json').read_text())['cases'][0]['initial'];(TMP/'code.bin').write_bytes(code_bytes(micro))
    for source,name in (('audit_tape_micro.cpp','native'),('micro_line_check.cpp','checker')):subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    summaries=[];queries=steps=0;all_requests={};first=None
    for obs in data['observations']:
        r=json.loads(artifact(obs['artifact']));need(r['case']==next(c for c in data['cases'] if c['id']==obs['case']) and r['mode']==obs['mode'] and r['repetition']==obs['repetition'],'cold assertion/method binding');requests=tree(r)
        for k in ('status','queries','nodes','seconds','cold_seconds','found'):need(r[k]==obs[k],'observation '+k)
        for request,rec in zip(requests,r['records']):
            initial=initial_for(micro,template,request);(TMP/'input.bin').write_bytes(input_bytes(initial));need(sha(TMP/'input.bin')==rec['input_sha256'],'full initial payload and frame');native=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',r['limits']['micro_steps']))
            for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(native[k])==str(rec['result'][k]),'independent complete native replay '+k)
            need(rec['result']['start']==micro['start'] and sha(TMP/'output.bin')==rec['output_sha256'],'true start and full output');queries+=1;steps+=native['micro_steps']
            if native['status'] in ('accepted','rejected'):
                try:logical=whole_replay(request)['status']
                except ValueError:logical='rejected'
                need(logical==native['status'],'independent logical cross-check')
            if rec['query_target']=='fixed_assertion' and native['status']=='accepted':all_requests[pin(request)]=request
        if first is None and r['found']:first=r
        summaries.append(dict(case=obs['case'],mode=obs['mode'],repetition=obs['repetition'],status=r['status'],queries=len(requests)));print(obs['artifact']['name'],'replayed',len(requests),flush=True)
    certificates=[]
    for row in data['certificates']:
        need(row['request_sha256'] in all_requests and row['request']==all_requests[row['request_sha256']],'proof came from true-start native discovery');initial=initial_for(micro,template,all_requests[row['request_sha256']]);need(initial==row['initial'],'whole proof boot frame')
        (TMP/'input.bin').write_bytes(input_bytes(initial));(TMP/'grammar.bin').write_bytes(artifact(row['grammar']));events=[json.loads(v) for v in artifact(row['events']).splitlines()];write_cuts([e['node'] for e in events if e['kind']=='fragment'],TMP/'observed.bin');checked=run(TMP/'checker',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'output.bin',10**9,1500000000,TMP/'root.json',TMP/'observed.bin'))
        need(checked['status']=='checked_response' and checked['result']=='accepted' and sha(TMP/'output.bin')==row['output_sha256'],'fresh independent full response derivation');root=json.loads((TMP/'root.json').read_text());need(root==json.loads(artifact(row['responses'])),'all independently derived interfaces');chain=checked_chain(row,micro,events,root);need(chain['final']==row['output'],'actual decoded whole proof and contexts');certificates.append(dict(name=row['name'],request_sha256=row['request_sha256'],lines=chain['lines'],contexts=chain['contexts'],fragments=chain['fragments'],checked=checked));print(row['name'],'native lines derived',len(chain['lines']),flush=True)
    corruptions=mutations(first);data_out=dict(version='certificate-boundary-audit-001',status='passed',producer_sha256=sha(DOCS/'certificate-boundary-001.json.gz'),source_sha256=sha(HERE/'audit_certificate_boundary.py'),observations=summaries,queries=queries,micro_steps=steps,certificates=certificates,mutations_rejected=corruptions,seconds=time.perf_counter()-began,prefix_pruning_scope='For the pinned proof loop, theory/signature, no blocks/open premises and backward-only references are constant. Each command checks against earlier proved formulas. Prefix target equals its last formula, so rejection cannot be repaired by appending later commands. This source-level argument and finite differential checks do not establish a universal compiler/kernel soundness theorem.')
    (DOCS/'certificate-boundary-audit-001.json.gz').write_bytes(gzip.compress(packed(data_out),mtime=0));print('audit complete',queries,round(data_out['seconds'],3),flush=True)
if __name__=='__main__':main()
