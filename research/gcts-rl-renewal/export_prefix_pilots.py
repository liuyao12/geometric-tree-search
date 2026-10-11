"""Export the audited negative pilot without replaying or changing its search."""
import ast,copy,gzip,hashlib,json,shutil
from pathlib import Path
from audit_semantic_inventory import need,same,pin,initial,advance,LiteralDomains
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
DOC=ROOT/'docs/research/gcts-rl-renewal';OUT=ROOT/'.gcts-active/certified-prefix-markings-20261011'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def put(name,raw):
    p=DOC/name;p.write_bytes(raw)
    return dict(name=name,sha256=sha(p),bytes=len(raw))
def closure():
    found={};pending=['prefix_failure_markings','audit_prefix_failure_markings','run_prefix_failure_pilot',
        'run_prefix_consumer_pilot','prefix_failure_differential','test_prefix_failure_markings',
        'audit_prefix_pilots','export_prefix_pilots']
    while pending:
        name=pending.pop();p=HERE/(name+'.py')
        if name in found or not p.exists():continue
        found[name]=sha(p)
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node,ast.Import):pending.extend(n.name.split('.')[0] for n in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
    return {n+'.py':v for n,v in sorted(found.items())}
def initial_census(spec,model):
    inventory={tuple(c['key']):c for c in model['placements']};s=initial(spec,model)
    if 'initial_marks' in model:s['marks'].update({tuple(p):v for p,v in model['initial_marks']})
    enumerate_domains=LiteralDomains(inventory);before=enumerate_domains(s);forced=[]
    while True:
        domains=enumerate_domains(s)
        if not domains or any(not cs for cs in domains.values()):break
        singles=[p for p,cs in domains.items() if len(cs)==1]
        if not singles:break
        p=min(singles,key=lambda p:(s['generations'][p],p));key=domains[p][0]
        forced.append(key);s=advance(inventory[key],s)
    choice=None if not domains or any(not cs for cs in domains.values()) else min(domains,key=lambda p:(s['generations'][p],len(domains[p]),p))
    return dict(initial=sum(map(len,before.values())),forced=forced,
        first_point=choice,first_candidates=domains.get(choice,[]),
        roots=[dict(point=p,original_count=len(cs),keys=cs) for p,cs in sorted(domains.items())])
def build():
    audit=json.loads((OUT/'audit.json').read_text());need(audit['status']=='passed','completed independent audit')
    need(audit['source_sha256']==sha(HERE/'audit_prefix_pilots.py'),'auditor binding')
    summary=json.loads((OUT/'pilot-summary.json').read_text())
    view=dict(version='certified-prefix-reader-001',cases=[],audit=audit,
        plan=json.loads((OUT/'plan.json').read_text()),artifacts=[],
        source_closure=closure(),scope='Audited exploratory paired preprocessing study. Three fresh failure catalogs; native admissions, four semantic families and frozen RL weights are reused from Notebook 63. No new RL training, cold timing comparison or learned speedup.')
    for name in ('two-premise','pa-universal-equality','renamed-five'):
        original_path=OUT/'pilot-output-only'/(name+'-pilot.json.gz');consumer_path=OUT/(name+'-consumer-pilot.json.gz')
        a=load(original_path);b=load(consumer_path)
        checked=next(c for c in audit['cases'] if c['case']==name)
        need((sha(original_path),sha(consumer_path))==(checked['original_sha256'],checked['consumer_sha256']),'audited artifact hashes')
        refs={variant:put('certified-prefix-001-'+name+'-'+variant+'.json.gz',path.read_bytes())
            for variant,path in (('output',original_path),('consumer',consumer_path))}
        view['artifacts'].extend(refs.values())
        original=next(r['model'] for r in a['results'] if not r['marked']);marked=b['results'][0]['model']
        inventory={tuple(c['key']):c for c in original['placements']}
        decorated={tuple(c['key']):c for c in marked['placements']};samples=[]
        failures=marked['failure_overlay']['failures']
        for f in failures:
            support=[inventory[tuple(k)] for k in f['affected_keys']]
            representatives=[]
            for kind in ('command','guard','lemma_input'):
                candidates=[c for c in support if c['kind']==kind]
                if candidates:representatives.append(decorated[tuple(max(candidates,key=lambda c:c['slot'])['key'])])
            samples.append(dict(**f,support=[dict(key=c['key'],slot=c['slot'],kind=c['kind']) for c in support],
                representatives=representatives))
        probes=[dict(id=p['id'],slot=p['slot'],formula=p['formula'],label=p['label'],
            status=p['search']['status'],metrics=p['search']['metrics'],seconds=p['search']['seconds'],
            lift_sha256=p['lift']['sha256'],checked=p['independent_check']) for p in a['learning']['probes']]
        r=next(r for r in b['results'] if r['mode']=='fixed');q=next(rec for rec in b['records'] if rec['id']==r['native_query'])
        old_census=initial_census(a['case'],original);new_census=initial_census(a['case'],marked)
        changed=[]
        new_roots={tuple(row['point']):row for row in new_census['roots']}
        for row in old_census['roots']:
            new=new_roots[tuple(row['point'])]
            if row['keys']!=new['keys']:changed.append(dict(point=row['point'],before=len(row['keys']),after=len(new['keys'])))
        census=dict(initial_before=old_census['initial'],initial_after=new_census['initial'],
            forced_before=len(old_census['forced']),forced_after=len(new_census['forced']),
            same_forced_sequence=old_census['forced']==new_census['forced'],
            first_point=old_census['first_point'],same_first_point=old_census['first_point']==new_census['first_point'],
            same_first_candidates=old_census['first_candidates']==new_census['first_candidates'],changed_roots_after_forcing=changed)
        need(census['same_first_point'] and census['same_first_candidates'],'diagnosis first-choice equality')
        learning=next(s for s in summary['cases'] if s['case']==name)
        selected=set(map(tuple,r['search']['placements']))
        view['cases'].append(dict(id=name,spec=a['case'],basis=a['compiled']['basis'],arity=original['arity'],
            inventory=a['inventory'],certificate=a['certificate'],probes=probes,failures=samples,
            learning_seconds=learning['learning_seconds'],observations=checked['observations'],
            native=[{k:rec[k] for k in ('id','request_sha256','input_sha256','output_sha256','result')} for rec in b['records']],
            proof=r['search']['proof'],selected=[c for c in marked['placements'] if tuple(c['key']) in selected],
            proof_query=q['id'],census=census,artifacts=refs))
        print('exported',name,len(probes),'queries',len(samples),'failure ports',flush=True)
    view['artifacts'].append(put('certified-prefix-audit-001.json.gz',gzip.compress(json.dumps(audit,separators=(',',':')).encode(),mtime=0)))
    source_pin=put('certified-prefix-source-closure-001.json',(json.dumps(view['source_closure'],indent=2)+'\n').encode())
    view['artifacts'].append(source_pin)
    for name in ('prefix_failure_markings.py','audit_prefix_failure_markings.py','run_prefix_failure_pilot.py'):
        target=HERE/'prefix_output_only_001'/name;target.parent.mkdir(exist_ok=True)
        shutil.copyfile(OUT/'pilot-output-only'/name,target)
    view['archived_sources']={name:sha(HERE/'prefix_output_only_001'/name) for name in
        ('prefix_failure_markings.py','audit_prefix_failure_markings.py','run_prefix_failure_pilot.py')}
    ref=put('certified-prefix-reader-001.json',(json.dumps(view,separators=(',',':'))+'\n').encode())
    (OUT/'export.json').write_text(json.dumps(ref,indent=2)+'\n')
    print('reader',ref['bytes'],'bytes',ref['sha256'],flush=True)
if __name__=='__main__':build()
