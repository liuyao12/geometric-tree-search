"""Independent reconstruction of every fixed-context local compaction.

No compaction or new catalog producer imports. Earlier exact formulas are
located by equality in a list, dependencies are sliced in reverse order, and
the complete local proof is separately replayed under its actual premise list.
This establishes preparation conformance only; it cannot authorize native use.
"""
import copy,gc,gzip,hashlib,json,resource,time
from pathlib import Path
from audit_semantic_proofs import whole_replay

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011'
def need(t,m):
    if not t:raise ValueError(m)
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def refs(row):
    need(row['rule']!='block','no nested local contexts');return ['antecedent','implication'] if row['rule']=='mp' else ['source'] if row['rule']=='generalize' else []
def reconstructed(d):
    proof=[];positions=[];formulas=[]
    for j,original in enumerate(d['proof']):
        row=copy.deepcopy(original)
        if row['rule']=='assumption':need(type(row['index']) is int and 0<=row['index']<len(d['premises']) and row['formula']==d['premises'][row['index']],'fixed premise context')
        for field in refs(row):need(type(row[field]) is int and 0<=row[field]<j,'prior dependency');row[field]=positions[row[field]]
        if row['formula'] in formulas:k=formulas.index(row['formula'])
        else:k=len(proof);proof.append(row);formulas.append(row['formula'])
        positions.append(k)
    required={positions[-1]}
    for j in range(positions[-1],-1,-1):
        if j in required:required.update(proof[j][field] for field in refs(proof[j]))
    indices=sorted(required);mapping={j:i for i,j in enumerate(indices)};output=[]
    for j in indices:
        row=copy.deepcopy(proof[j])
        for field in refs(row):row[field]=mapping[row[field]]
        output.append(row)
    value=copy.deepcopy(d);value['proof']=output;return value
def main():
    began=time.perf_counter();plan=json.loads((OUT/'compaction-audit-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'compaction-preparation.json').read_text());need(summary['status']=='prepared_host_audit_only' and summary['native_queries']==0,'preparation only')
    for path,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,'frozen source '+path)
    result=dict(status='checking',native_queries=0,variants=[])
    (OUT/'compaction-preparation-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    for lane in base['variants']:
        original=load(OUT/(lane+'-core.json.gz'));compact=load(OUT/(lane+'-compact-core.json.gz'));need({k:v for k,v in original.items() if k!='definitions'}=={k:v for k,v in compact.items() if k not in ('definitions','preparation_transform')},'complete logical inventory unchanged');need(len(original['definitions'])==len(compact['definitions']),'same definitions')
        for j,(d,actual) in enumerate(zip(original['definitions'],compact['definitions'])):
            expected=reconstructed(d);need(expected==actual,'exact independently compacted local definition');taut=['imp',['bot'],['bot']];q=dict(protocol='gcts-fol-1',theory=base['case']['theory'],blocks=[actual],proof=[dict(rule='tautology',formula=taut)],target=taut);need(whole_replay(q)['status']=='accepted','full local proof under fixed premises')
            if j%32==0:
                result.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
                (OUT/'compaction-preparation-audit.json').write_text(json.dumps(result,indent=2)+'\n')
                if result['seconds']>plan['ceilings']['seconds']:raise TimeoutError('unknown_compaction_audit_time_budget')
                if result['peak_rss_bytes']>plan['ceilings']['rss_bytes']:raise MemoryError('unknown_compaction_audit_memory_budget')
        result['variants'].append(dict(lane=lane,independently_reconstructed_definitions=len(compact['definitions']),commands=sum(len(d['proof']) for d in compact['definitions']),native_authority='not established'));print('compaction preparation audit',lane,flush=True)
        del original,compact,d,actual,expected,q;gc.collect()
    result.update(status='passed_compaction_preparation_audit_only',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scope='Every local proof independently shared/sliced and fully logically replayed within its unchanged premise context. Complete rules, basis, theory, target and interfaces preserved. Native admission still required.')
    (OUT/'compaction-preparation-audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
    try:main()
    except (TimeoutError,MemoryError,ValueError) as e:
        p=OUT/'compaction-preparation-audit.json';r=json.loads(p.read_text()) if p.exists() else dict(native_queries=0,variants=[]);r.update(status=str(e),failure_type=type(e).__name__,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);p.write_text(json.dumps(r,indent=2)+'\n');raise
