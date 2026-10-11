"""Compact audited projection and exact public source/artifact bindings."""
import ast,gzip,hashlib,json
from pathlib import Path
from certificate_boundary_search import canonical,digest
from native_receptor_points import assignment

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/conditional-attachments-20261011'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(gzip.decompress(p.read_bytes()))


def sources():
    pending=['conditional_failure_markings','audit_conditional_failure_markings','run_conditional_failure_pilot',
             'audit_conditional_pilot','test_conditional_failure_markings','test_conditional_provenance','export_conditional_pilot'];found={}
    while pending:
        n=pending.pop();p=HERE/(n+'.py')
        if n in found or not p.exists():continue
        found[n]=sha(p)
        for a in ast.walk(ast.parse(p.read_text())):
            if isinstance(a,ast.Import):pending.extend(x.name.split('.')[0] for x in a.names)
            elif isinstance(a,ast.ImportFrom) and a.module:pending.append(a.module.split('.')[0])
    out={str((HERE/(n+'.py')).relative_to(ROOT)):h for n,h in sorted(found.items())}
    for name in ('boundary_oracle.cpp','audit_tape_micro.cpp'):
        out[str((HERE/name).relative_to(ROOT))]=sha(HERE/name)
    for p in sorted((HERE/'conditional_provenance_001').glob('*.py')):
        out[str(p.relative_to(ROOT))]=sha(p)
    return out


def main():
    audit=json.loads((OUT/'audit.json').read_text());assert audit['status']=='passed'
    summary=json.loads((OUT/'summary.json').read_text());assert summary['status']=='paired_pilot_complete'
    plan=json.loads((OUT/'plan.json').read_text());cases=[];artifacts=[];native=[]
    for name in plan['cases']:
        path=OUT/(name+'-pilot.json.gz');raw=load(path)
        check=next(c for c in audit['cases'] if c['case']==name)
        assert sha(path)==check['artifact_sha256']
        target=DOC/('conditional-001-'+name+'.json.gz');target.write_bytes(path.read_bytes())
        artifacts.append(dict(path=target.name,sha256=sha(target),bytes=target.stat().st_size))
        original=raw['models']['original'];lookup={tuple(c['key']):c for c in original['placements']}
        marked={tuple(c['key']):c for c in raw['models']['conditional']['placements']}
        values={k:dict((tuple(p),v) for p,v in c['marks']) for k,c in lookup.items()}
        writers=[]
        for j in range(raw['case']['length']):
            for f in raw['compiled']['basis']:
                word=assignment(j,'formula',f)
                keys=[k for k,v in sorted(values.items()) if all(v.get(p)==a for p,a in word)]
                if keys:writers.append(dict(slot=j,formula=f,word=word,keys=keys))
        probes=[]
        singles={(p['slot'],digest(p['formula'])):p['label'] for p in raw['unary_learning']['probes']}
        for p in raw['learning']['probes']:
            probes.append(dict(id=p['id'],slots=p['slots'],formulas=p['formulas'],label=p['label'],
                individual_labels=[singles[j,digest(f)] for j,f in zip(p['slots'],p['formulas'])],
                genuine=p['id'] in raw['genuine_conditional_negatives'],
                teacher_status=p['search']['status'],teacher_metrics=p['search']['metrics'],
                lift_sha256=p['lift']['sha256'],teacher_sha256=digest(p['search']),
                checked_nodes=p['independent_check']['nodes']))
        failures=[]
        for f in raw['models']['conditional']['conditional_overlay']['failures']:
            reps=[]
            for side in ('left','right','joint'):
                keys=f[side+'_keys']
                if keys:
                    key=tuple(keys[0]);c=lookup[key];m=marked[key]
                    reps.append(dict(side=side,key=key,kind=c['kind'],slot=c['slot'],
                        occupancy=c['occupancy'],original_marks=c['marks'],marked_marks=m['marks']))
            failures.append(dict(**f,representatives=reps))
        proofs=[]
        for r in raw['results']:
            if r['search']['proof'] is None:continue
            layer=raw['models'][r['layer']];tiles={tuple(c['key']):c for c in layer['placements']}
            selected=[tiles[tuple(k)] for k in r['search']['placements']]
            proofs.append(dict(id=r['layer']+'-'+r['mode'],layer=r['layer'],mode=r['mode'],
                proof=r['search']['proof'],tiles=selected,initial_marks=layer['initial_marks'],
                native_query=r['native_query'],source='gcts'))
        if raw['smt_control'] and raw['smt_control']['proof']:
            r=raw['smt_control'];selected=[lookup[tuple(k)] for k in r['placements']]
            proofs.append(dict(id='original-z3',layer='original',mode='z3',proof=r['proof'],tiles=selected,
                initial_marks=original['initial_marks'],native_query=r['native_query'],source='z3'))
        native.extend(dict(id=q['id'],status=q['result']['status'],purpose=q['purpose'],
            request=q['request'],request_sha256=q['request_sha256'],input_sha256=q['input_sha256'],
            output_sha256=q['output_sha256'],micro_steps=q['result']['micro_steps']) for q in raw['records'])
        cases.append(dict(id=name,title=raw['case']['title'],spec=raw['case'],basis=raw['compiled']['basis'],
            tautologies=raw['compiled']['tautologies'],registry=raw['inventory'],row_pairs=raw['learning']['row_pairs'],
            unary_counts=raw['unary_learning']['counts'],pair_counts=raw['learning']['counts'],
            unary_probes=[dict(id=p['id'],slot=p['slot'],formula=p['formula'],label=p['label'],
                teacher_status=p['search']['status'],checked_nodes=p['independent_check']['nodes'])
                for p in raw['unary_learning']['probes']],
            unary_learning_seconds=raw['unary_learning']['seconds'],pair_learning_seconds=raw['learning']['seconds'],
            context_sha256=raw['learning']['context_sha256'],learning_sha256=digest(raw['learning']),
            certificate=raw['certificate'],probes=probes,writers=writers,failures=failures,proofs=proofs,
            observations=check['observations'],overlay_checks=check['overlay_checks'],root_domains=check['root_domains'],
            smt_control={k:v for k,v in raw['smt_control'].items() if k not in ('smtlib','proof','placements')} if raw['smt_control'] else None,
            reused_context=raw['reused_context'],artifact=target.name))
        cases[-1]['fresh_native_seconds']=sum(q['seconds'] for q in raw['records'])
    audit_path=DOC/'conditional-audit-001.json.gz';audit_path.write_bytes(gzip.compress(canonical(audit),mtime=0))
    artifacts.append(dict(path=audit_path.name,sha256=sha(audit_path),bytes=audit_path.stat().st_size))
    plan_path=DOC/'conditional-plan-001.json';plan_path.write_bytes(canonical(plan)+b'\n')
    artifacts.append(dict(path=plan_path.name,sha256=sha(plan_path),bytes=plan_path.stat().st_size))
    closure=sources();closure_path=DOC/'conditional-source-closure-001.json'
    closure_path.write_text(json.dumps(dict(version='conditional-source-closure-001',files=closure),indent=2)+'\n')
    artifacts.append(dict(path=closure_path.name,sha256=sha(closure_path),bytes=closure_path.stat().st_size))
    data=dict(version='conditional-reader-001',pilot_seconds=summary['seconds'],audit={k:v for k,v in audit.items() if k not in ('cases','pilot_sources')},
        cases=cases,native=native,artifacts=artifacts,source_closure=closure,
        scope='Compact display projection of independently reconstructed pair teachers, original word writers, exact extra values and selected proof rows. Browser projection checks supplement, and do not execute, the complete tree/native audit.')
    reader=DOC/'conditional-reader-001.json';reader.write_bytes(canonical(data)+b'\n')
    report=dict(status='passed',cases=len(cases),pairs=sum(len(c['probes']) for c in cases),
        observations=sum(len(c['observations']) for c in cases),proofs=sum(len(c['proofs']) for c in cases),
        bytes=reader.stat().st_size,reader_sha256=sha(reader),source_files=len(closure))
    (OUT/'export.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
