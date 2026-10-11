"""Generic DAG sharing inside a single fixed local-premise context.

Every input line is first validated. The transform reuses only an earlier exact
formula, remaps strict-prior dependencies, then removes unreachable commands.
It never shares across definitions or premise lists, inserts inferences, changes
the theory/interface, or supplies a theorem-proof path. Native admission remains
necessary for the resulting definition bytes.
"""
import copy,gzip,hashlib,json,resource,time
from pathlib import Path
from certificate_boundary_search import canonical
from audit_semantic_proofs import whole_replay

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011'
def need(t,m):
    if not t:raise ValueError(m)
def refs(row):
    rule=row['rule'];need(rule in ('mp','generalize','assumption','axiom','tautology','refl','instantiate','distribute','eq_subst','induction'),'primitive local command required')
    return ('antecedent','implication') if rule=='mp' else ('source',) if rule=='generalize' else ()
def compact(definition):
    source=definition['proof'];premises=definition['premises'];need(source and source[-1]['formula']==definition['conclusion'],'exact declared local conclusion');commands=[];images=[];known={}
    for j,command in enumerate(source):
        row=copy.deepcopy(command)
        for k in refs(row):
            need(type(row[k]) is int and 0<=row[k]<j,'strict-prior dependency');row[k]=images[row[k]]
        if row['rule']=='assumption':
            k=row['index'];need(type(k) is int and 0<=k<len(premises) and row['formula']==premises[k],'exact assumption in the fixed premise context')
        word=canonical(row['formula'])
        if word in known:i=known[word]
        else:i=len(commands);known[word]=i;commands.append(row)
        images.append(i)
    required=set();todo=[images[-1]]
    while todo:
        i=todo.pop()
        if i in required:continue
        required.add(i);todo.extend(commands[i][k] for k in refs(commands[i]))
    remap={i:j for j,i in enumerate(sorted(required))};proof=[]
    for i in sorted(required):
        row=copy.deepcopy(commands[i])
        for k in refs(row):row[k]=remap[row[k]]
        proof.append(row)
    output=copy.deepcopy(definition);output['proof']=proof;need(proof[-1]['formula']==definition['conclusion'],'terminal formula preserved');return output
def fixture():
    f=['eq',['var','x'],['var','x']];d=dict(name='fixture',premises=[f],conclusion=f,proof=[dict(rule='assumption',formula=f,index=0),dict(rule='refl',formula=f),dict(rule='tautology',formula=['imp',f,f]),dict(rule='mp',formula=f,antecedent=1,implication=2)])
    need(compact(d)['proof']==[d['proof'][0]],'same fixed premise context may reuse an exact formula')
    bad=copy.deepcopy(d);bad['proof'][0]['index']=1
    try:compact(bad)
    except ValueError:pass
    else:raise ValueError('foreign premise accepted')
    bad=copy.deepcopy(d);bad['proof'][-1]['antecedent']=-1
    try:compact(bad)
    except ValueError:pass
    else:raise ValueError('negative dependency accepted')
def main():
    began=time.perf_counter();plan=json.loads((OUT/'compaction-preparation-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());need(json.loads((OUT/'audit.json').read_text())['status']=='passed_preparation_audit_only','prior complete preparation audit')
    for path,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,'frozen compaction source '+path)
    fixture();summary=dict(status='preparing',native_queries=0,variants=[])
    for lane in base['variants']:
        c=json.loads(gzip.decompress((OUT/(lane+'-core.json.gz')).read_bytes()));old=c['definitions'];start=time.perf_counter();updated=[]
        for j,d in enumerate(old):
            new=compact(d);need({k:v for k,v in new.items() if k!='proof'}=={k:v for k,v in d.items() if k!='proof'},'unchanged local interface')
            taut=['imp',['bot'],['bot']];request=dict(protocol='gcts-fol-1',theory=base['case']['theory'],blocks=[new],proof=[dict(rule='tautology',formula=taut)],target=taut);need(whole_replay(request)['status']=='accepted','compacted full local definition logical audit');updated.append(new)
            if j%32==0:
                if time.perf_counter()-began>plan['ceilings']['seconds']:raise TimeoutError('unknown_compaction_preparation_time_budget')
                if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>plan['ceilings']['rss_bytes']:raise MemoryError('unknown_compaction_preparation_memory_budget')
        c['definitions']=updated;c['preparation_transform']='exact-formula sharing and dependency slicing within each unchanged fixed premise context; native authority not yet established';(OUT/(lane+'-compact-core.json.gz')).write_bytes(gzip.compress(json.dumps(c,separators=(',',':')).encode(),mtime=0));stats=dict(lane=lane,definitions=len(old),old_commands=sum(len(d['proof']) for d in old),new_commands=sum(len(d['proof']) for d in updated),old_definition_json_bytes=sum(len(canonical(d)) for d in old),new_definition_json_bytes=sum(len(canonical(d)) for d in updated),max_commands=max(len(d['proof']) for d in updated),max_definition_json_bytes=max(len(canonical(d)) for d in updated),changed_definitions=sum(d!=q for d,q in zip(old,updated)),seconds=time.perf_counter()-start);summary['variants'].append(stats);(OUT/'compaction-preparation.json').write_text(json.dumps(summary,indent=2)+'\n');print(stats,flush=True)
    summary.update(status='prepared_host_audit_only',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scope='Same complete logical interfaces/theory/target. All compact local command lists pass full host replay; no native admission or theorem search yet.')
    (OUT/'compaction-preparation.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
