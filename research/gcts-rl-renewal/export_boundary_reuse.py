"""Publish a compact, audited boundary comparison and inspectable proof rows."""
import ast,gzip,hashlib,json
from pathlib import Path
from certificate_boundary_search import canonical,digest
from native_receptor_points import assignment

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/boundary-reuse-20261011'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(gzip.decompress(path.read_bytes()))


def sources(plan):
    out=dict(plan['prior_source_closure']);pending=['export_boundary_reuse',*map(lambda p:Path(p).stem,plan['source_sha256'])]
    seen=set()
    while pending:
        name=pending.pop();path=HERE/(name+'.py')
        if name in seen or not path.exists():continue
        seen.add(name);out[path.relative_to(ROOT).as_posix()]=sha(path)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
    for name in ('boundary_oracle.cpp','audit_tape_micro.cpp','test_boundary_reuse_reader.js'):
        out[(HERE/name).relative_to(ROOT).as_posix()]=sha(HERE/name)
    out['docs/research/gcts-rl-renewal/boundary-reuse.js']=sha(DOC/'boundary-reuse.js')
    return dict(sorted(out.items()))


def main():
    audit=json.loads((OUT/'audit.json').read_text());assert audit['status']=='passed'
    summary=json.loads((OUT/'summary.json').read_text());assert summary['status']=='complete'
    plan=json.loads((OUT/'plan.json').read_text());cases=[];artifacts=[]
    for config in plan['configs']:
        path=OUT/(config['id']+'.json.gz');raw=load(path)
        check=next(c for c in audit['cases'] if c['case']==config['id']);assert sha(path)==check['artifact_sha256']
        target=DOC/('boundary-reuse-001-'+config['id']+'.json.gz');target.write_bytes(path.read_bytes())
        artifacts.append(dict(path=target.name,sha256=sha(target),bytes=target.stat().st_size))
        original=raw['models']['original'];values={tuple(c['key']):dict((tuple(p),v) for p,v in c['marks']) for c in original['placements']}
        writers=[]
        for j in sorted({s for p in raw['constraints']['negatives'] for s in p['slots']}):
            for f in raw['compiled']['basis']:
                word=assignment(j,'formula',f);keys=[k for k,m in sorted(values.items()) if all(m.get(p)==v for p,v in word)]
                if keys:writers.append(dict(slot=j,formula=f,word=word,keys=keys))
        failures=[{k:v for k,v in f.items() if k!='assignments'} for f in raw['models']['point']['conditional_overlay']['failures']]
        observations=[]
        for result,observed in zip(raw['results'],check['observations']):
            assert all(result[k]==observed[k] for k in ('layer','mode','repetition','native_query','cached_native_acceptance'))
            out=result['search'];layer=result['layer'];model=raw['models'][layer]
            lookup={tuple(c['key']):c for c in model['placements']}
            selected=[lookup[tuple(k)] for k in out['placements']]
            observations.append(dict(**observed,id=layer+'-'+result['mode']+'-r'+str(result['repetition']),
                proof=out['proof'],tiles=selected,initial_marks=model['initial_marks'],
                semantic_tree_sha256=None if result['mode']!='base' or layer=='original' else
                    next(x['sha256'] for x in check['equivalence'] if x['repetition']==result['repetition']),
                complete_tree_sha256=digest(out['tree']),model_sha256=digest(model)))
        cases.append(dict(id=config['id'],title=raw['case']['title'],spec=raw['case'],basis=raw['compiled']['basis'],variables=raw['compiled']['variables'],
            tautologies=raw['compiled']['tautologies'],registry=raw['inventory'],source=raw['source'],
            source_counts=raw['constraints']['counts'],source_learning_sha256=raw['constraints']['learning_sha256'],
            transfer_certificate=raw['transfer_certificate'],transfer_seconds=raw['transfer_seconds'],
            source_collection_seconds=raw['source_collection_seconds'],writers=writers,failures=failures,
            observations=observations,equivalence=check['equivalence'],artifact=target.name))
    native=load(OUT/'native-records.json.gz');target=DOC/'boundary-reuse-native-001.json.gz';target.write_bytes((OUT/'native-records.json.gz').read_bytes())
    artifacts.append(dict(path=target.name,sha256=sha(target),bytes=target.stat().st_size))
    native_display=[dict(id=q['id'],request=q['request'],status=q['result']['status'],micro_steps=q['result']['micro_steps'],
        request_sha256=q['request_sha256'],input_sha256=q['input_sha256'],output_sha256=q['output_sha256'],seconds=q['seconds']) for q in native]
    target=DOC/'boundary-reuse-audit-001.json.gz';target.write_bytes(gzip.compress(canonical(audit),mtime=0))
    artifacts.append(dict(path=target.name,sha256=sha(target),bytes=target.stat().st_size))
    target=DOC/'boundary-reuse-plan-001.json';target.write_bytes(canonical(plan)+b'\n')
    artifacts.append(dict(path=target.name,sha256=sha(target),bytes=target.stat().st_size))
    closure=sources(plan);target=DOC/'boundary-reuse-source-closure-001.json'
    target.write_text(json.dumps(dict(version='boundary-reuse-source-closure-001',files=closure),indent=2)+'\n')
    artifacts.append(dict(path=target.name,sha256=sha(target),bytes=target.stat().st_size))
    data=dict(version='boundary-reuse-reader-001',cases=cases,native=native_display,
        limits=plan['search_limits'],repetitions=plan['repetitions'],pilot_seconds=summary['seconds'],
        audit={k:v for k,v in audit.items() if k not in ('cases','source_sha256','prior_source_closure')},
        source_closure=closure,artifacts=artifacts,
        scope='Compact projection of independently audited boundary transfers, direct/point base-tree equivalence, all measured observations and selected native-checked proof regions. Browser checks cover this projection; native computations and full tree replay run outside the browser.')
    target=DOC/'boundary-reuse-reader-001.json';target.write_bytes(canonical(data)+b'\n')
    report=dict(status='passed',cases=len(cases),observations=sum(len(c['observations']) for c in cases),
        proofs=sum(o['proof'] is not None for c in cases for o in c['observations']),
        reader_bytes=target.stat().st_size,reader_sha256=sha(target),source_files=len(closure))
    (OUT/'export.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
