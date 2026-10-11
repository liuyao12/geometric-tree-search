"""Fresh immutable activation of each already bounded13row phase."""
import argparse
import ast
import datetime
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'.gcts-active/commutativity13-20261011'


def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def closure(roots):
    done=set();todo=roots+['commutativity13_phase_freeze']
    while todo:
        n=todo.pop();p=HERE/(n+'.py')
        if n in done or not p.exists():continue
        done.add(n)
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node,ast.Import):todo.extend(v.name.split('.')[0] for v in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:todo.append(node.module.split('.')[0])
    return {str((HERE/(n+'.py')).relative_to(ROOT)):h(HERE/(n+'.py')) for n in sorted(done)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['preflight-audit','execution','tree-audit']);args=parser.parse_args()
    first=json.loads((OUT/'preflight-plan.json').read_text())
    for p,v in {**first['source_sha256'],**first['input_sha256']}.items():
        if h(ROOT/p)!=v:raise ValueError('original exact preflight freeze '+p)
    inputs=dict(first['input_sha256']);inputs[str((OUT/'preflight-plan.json').relative_to(ROOT))]=h(OUT/'preflight-plan.json')
    names=['preflight-summary.json','model13.json.gz','binding13.json.gz','static13.json.gz','correspondence.json.gz','fixtures.json.gz','fixture-base.json.gz','fixture-fixed.json.gz','fixed-r1-events.json.gz','fixed-r2-events.json.gz','fixed-r1-events-receipt.json','fixed-r2-events-receipt.json']
    if args.phase=='preflight-audit':
        filename='preflight-audit-plan.json';roots=['commutativity13_audit'];status='frozen_complete_independent_correspondence_and13model_audit'
        if json.loads((OUT/'preflight-summary.json').read_text())['status']!='complete_exact589event_and13row_fixture_correspondence_pending_independent_audit':raise ValueError('producer gate not resolved')
    elif args.phase=='execution':
        filename='execution-freeze.json';roots=['commutativity13_runner','commutativity13_tree_audit'];status='frozen_four_matched13row_observations'
        names+=['preflight-audit-plan.json','preflight-audit.json','fixed-r1-projection-audit.json','fixed-r2-projection-audit.json','external-model-correspondence.json']
        if json.loads((OUT/'preflight-audit.json').read_text())['status']!='passed_complete_exact_proposer_serialization_and13model_preflight':raise ValueError('independent preflight unresolved')
        if json.loads((OUT/'external-model-correspondence.json').read_text())['status']!='passed_exact_independent13point_model_hash':raise ValueError('external full-model gate unresolved')
    else:
        filename='tree-audit-plan.json';roots=['commutativity13_tree_audit'];status='frozen_independent_every_actual13row_tree_audit'
        names+=['preflight-audit-plan.json','preflight-audit.json','execution-freeze.json','search-summary.json']
        if json.loads((OUT/'search-summary.json').read_text())['status']!='complete_four_matched13_search_observations_pending_independent_audit':raise ValueError('four observation producer unresolved')
        for n in ('base-r1','fixed-r1','fixed-r2','base-r2'):names += [n+'-model.json.gz',n+'-search.json.gz',n+'-checkpoint.json',n+'-summary.json']
    path=OUT/filename
    if path.exists():raise ValueError('immutable phase freeze already exists')
    for n in names:inputs[str((OUT/n).relative_to(ROOT))]=h(OUT/n)
    source={**first['source_sha256'],**closure(roots)}
    zpath=OUT/(args.phase+'-sources.zip')
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in source:
            if p.endswith('.py'):z.write(ROOT/p,p)
    source[str(zpath.relative_to(ROOT))]=h(zpath)
    plan=dict(status=status,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=source,input_sha256=inputs,case=first['case'],
              observations=[dict(id=n,mode=n.split('-')[0],rep=int(n[-1])) for n in ('base-r1','fixed-r1','fixed-r2','base-r2')],
              boundary_rows=13,attempts_per_search=5000,seconds_per_search=60,producer_seconds=300,audit_seconds=300,rss_bytes=536870912,
              ordinary_word_or_witnesses_used=False,rl_training=False,native_target_queries_authorized=0,
              preservation='Unchanged153interfaces/94admitteddefinitions/fullpointgraph/globaldeadforcedgeneration/fallback/rollback. New13rowboundary and exactcostoptimization disclosed. Everyactualtree independently replayed.',
              source_timing_only_amendment='commutativity13_executor_search is byte-identical to correspondence-tested commutativity13_search except measurement/return of proposer initialization seconds; no scheduler/pool/feature/order alteration.',
              resource='No restart,sourceamendment,resourcewidening or nativequery authorization from an unknown gate. Totalphase time checked before each subprocess/query; any one-operation overshoot retained as unknown.')
    path.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(phase=args.phase,plan_sha256=h(path),sources=len(source),inputs=len(inputs))))

if __name__=='__main__':main()
