"""Independent proof DAG reconstruction, expansion and native input bindings.

No proposer, compactor or producer imports. All removed material is checked
before comparing the exact dependency transformation. Two finite optimized
controls also replay every tree instruction with independent semantics.
"""
import copy,hashlib,json,resource,struct,time
from pathlib import Path
from audit_serialized_kernel import replay
from audit_tree_kernel import packed,sha,need,audit_row,PINNED_PROGRAM_SHA256

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def pin(d):return sha({k:d[k] for k in ('protocol','theory','target')})
def refs(line):
    r=line['rule']
    return [line['antecedent'],line['implication']] if r=='mp' else [line['source']] if r=='generalize' else line['inputs'] if r=='block' else []
def transform(lines):
    representatives=[]
    for i,l in enumerate(lines):
        representatives.append(next((j for j in range(i) if lines[j]['formula']==l['formula']),i))
    keep=set()
    def visit(i):
        i=representatives[i]
        if i in keep:return
        keep.add(i)
        for j in refs(lines[i]):need(j<i,'strict earlier original dependency');visit(j)
    visit(len(lines)-1);order=sorted(keep);new={i:j for j,i in enumerate(order)};out=[]
    for i in order:
        l=copy.deepcopy(lines[i]);r=l['rule']
        if r=='mp':l.update(antecedent=new[representatives[l['antecedent']]],implication=new[representatives[l['implication']]])
        if r=='generalize':l['source']=new[representatives[l['source']]]
        if r=='block':l['inputs']=[new[representatives[j]] for j in l['inputs']]
        out.append(l)
    return out,dict(original_lines=len(lines),retained_lines=len(out),aliases=representatives,retained=order,old_to_new=[new.get(j) for j in representatives],root=representatives[-1],duplicates=sum(i!=j for i,j in enumerate(representatives)))
def audit_pair(original,c,expected_pin):
    need(pin(original)==expected_pin,'original external problem pin')
    a=replay(packed(original),expected_pin);need(a['status']=='accepted','every original line and block must check')
    need(c['status']=='accepted_compaction' and c['input_check']['status']=='accepted' and c['output_check']['status']=='accepted','compaction check status')
    need(c['input_check']['certificate_sha256']==sha(original) and c['output_check']['certificate_sha256']==sha(c['request']),'host exact byte checks')
    expected=copy.deepcopy(original);graphs=[]
    for b in expected['blocks']:
        b['proof'],g=transform(b['proof']);graphs.append(dict(name=b['name'],**g))
    expected['proof'],g=transform(expected['proof']);graphs.append(dict(name='root',**g))
    need(graphs==c['graphs'],'independent dependency/alias maps')
    live=set();pending=[l['name'] for l in expected['proof'] if l['rule']=='block'];by_name={b['name']:b for b in expected['blocks']}
    while pending:
        n=pending.pop()
        if n not in live:
            live.add(n);pending.extend(l['name'] for l in by_name[n]['proof'] if l['rule']=='block')
    need(c['removed_blocks']==[b['name'] for b in expected['blocks'] if b['name'] not in live],'removed checked definitions')
    expected['blocks']=[b for b in expected['blocks'] if b['name'] in live]
    need(expected==c['request'] and pin(expected)==expected_pin,'whole transformed request and unchanged interfaces')
    b=replay(packed(expected),expected_pin);need(b['status']=='accepted','independent optimized expansion')
    return dict(original_expanded_lines=a['expanded_lines'],compact_expanded_lines=b['expanded_lines'],schema_instances=b['schema_instances'])
def input_digest(code,request):
    nodes=[tuple(n) for n in code['nodes']];index={n:257+i for i,n in enumerate(nodes)}
    def pair(a,b):
        if (a,b) not in index:index[a,b]=257+len(nodes);nodes.append((a,b))
        return index[a,b]
    def word(items):
        p=256
        for a in reversed(items):p=pair(a,p)
        return p
    def text(s):return word(list(s.encode('utf-8','surrogatepass')))
    def encode(a):
        if type(a) is dict:
            keys=list(a);values=[encode(a[k]) for k in keys];return pair(0,word([pair(text(k),v) for k,v in zip(keys,values)]))
        if type(a) is list:return pair(1,word([encode(v) for v in a]))
        if type(a) is str:return pair(2,text(a))
        if type(a) is bool:return pair(5,int(a))
        if type(a) is int:return pair(3 if a>=0 else 4,word([1]*abs(a)))
        need(a is None,'exact syntax input');return pair(6,256)
    root=encode(json.loads(packed(request)));items=[0x47544931,root,len(nodes)]
    for a,b in nodes:items.extend((a,b))
    return hashlib.sha256(struct.pack('<'+'I'*len(items),*items)).hexdigest()
def native_binding(code,d,r):
    need(r['program_sha256']==PINNED_PROGRAM_SHA256==sha(code),'native fixed code pin')
    need(r['input_sha256']==input_digest(code,d),'independent native syntax heap pin')
    need(r['status'] in ('accepted','unknown_step_budget','unknown_resource_budget'),'expected native acceptance/resource result')
def main():
    began=time.perf_counter();path=DOCS/'proof-compaction-001.json';data=json.loads(path.read_text());old=json.loads((DOCS/'learned-proof-blocks-001.json').read_text())
    for n,h in data['sources'].items():need(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==h,'source '+n)
    for n,h in data['reused_artifacts'].items():need(hashlib.sha256((DOCS/n).read_bytes()).hexdigest()==h,'reused artifact '+n)
    requests={r['problem']['id']:r['result']['request'] for r in old['discovery']};requests.update({r['problem']+'/'+r['lane']:r['result']['request'] for r in old['evaluation']['runs'] if r['result']['status']=='accepted_proposal'})
    old_native={r['id']:r['result'] for r in old['native_tree_replay']['cases']};code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program'];results=[]
    need(len(data['cases'])==66 and {r['id'] for r in data['cases']}==set(requests),'66 actual found requests')
    for i,r in enumerate(data['cases']):
        d=requests[r['id']];need(r['original_certificate_sha256']==sha(d),'original witness pin');a=audit_pair(d,r['compaction'],r['problem_pin'])
        need(r['order']==(['original','compact'] if i%2==0 else ['compact','original']),'counterbalanced run order')
        for lane in ('original','compact'):
            native_binding(code,d if lane=='original' else r['compaction']['request'],r['native'][lane]);need(r['native'][lane]['status']=='accepted','full native acceptance')
        for k in ('steps','event_sha256','profile','peak_frames','heap_nodes','value'):need(r['native']['original'][k]==old_native[r['id']][k],'unchanged original full trace')
        results.append(dict(id=r['id'],**a))
    controls=[]
    for r in data['reference_controls']:
        row=next(x for x in data['cases'] if x['id']==r['id']);d=row['compaction']['request'];record=dict(payload_hex=packed(d).hex(),problem_pin=pin(d),check=r['check'],step_limit=50000000,heap_limit=2000000)
        actual=audit_row(code,record)
        for k in ('steps','event_sha256','profile','peak_frames','heap_nodes','value'):need(actual[k]==row['native']['compact'][k],'independent full reference/native control '+k)
        controls.append(dict(id=r['id'],steps=actual['steps'],event_sha256=actual['event_sha256']))
    base=data['cases'][0];original=requests[base['id']];mutations=[]
    for name,change in [('alias-map',lambda d:d['graphs'][-1]['aliases'].__setitem__(0,999)),('target',lambda d:d['request'].update(target=['bot'])),('theory',lambda d:d['request']['theory']['axioms'].update(invented=d['request']['target'])),('dependency',lambda d:d['request']['proof'][-1].update(source=999))]:
        wrong=copy.deepcopy(base['compaction']);change(wrong)
        try:audit_pair(original,wrong,base['problem_pin'])
        except ValueError:mutations.append(name)
        else:raise ValueError('mutation accepted '+name)
    data['independent_audit']=dict(cases=results,full_instruction_controls=controls,mutations_rejected=mutations,seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='All original and compact roots/definitions independently expanded, exact graph transformation and native input heaps reconstructed; complete independent tree execution on two optimized controls, not all 66 executions. Generic logical soundness and toolchain formalization remain open.')
    path.write_text(json.dumps(data,separators=(',',':'))+'\n');print('audited',len(results),data['independent_audit']['seconds'],flush=True)
if __name__=='__main__':main()
