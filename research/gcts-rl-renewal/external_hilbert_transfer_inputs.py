"""Exact frozen derived-premise assertions, without library or proof inputs."""
import copy,gzip,json
from pathlib import Path
from external_prover_inputs import Symbols,canonical,sha
from external_hilbert_run import validate_theory

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/external-hilbert-transfer-20261011'
SOURCE=ROOT/'.gcts-active/hilbert-boundary-transfer-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes())) if p.suffix=='.gz' else json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def build():
    plan=load(SOURCE/'plan.json');catalog=load(SOURCE/'declared-catalog.json.gz');audit=load(SOURCE/'audit.json')
    if audit['status']!='passed' or audit['production_outcome']!='complete' or catalog!=load(SOURCE/'catalog.json.gz'):raise ValueError('complete frozen native geometry authority')
    cases=[]
    for group in ('delayed-common','coupled-reverse'):
        variants=[c for c in plan['cases'] if c['group']==group]
        if len(variants)!=2 or variants[0]['theory']!=variants[1]['theory'] or variants[0]['target']!=variants[1]['target']:raise ValueError('short/sufficient must be identical assertions')
        spec=variants[0];validate_theory(spec)
        if len(spec['theory']['axioms'])!=4 or spec['theory']['schemas']:raise ValueError('exact four explicit axioms')
        cases.append(dict(group=group,spec=copy.deepcopy(spec),native_variants=copy.deepcopy(variants),native_theorem_sha256=sha(canonical(dict(theory=spec['theory'],target=spec['target'])))))
    return dict(cases=cases,native_audit_sha256=sha((SOURCE/'audit.json').read_bytes()),native_plan_sha256=sha((SOURCE/'plan.json').read_bytes()),scope='Two exact symbolic assertions, no coordinates, theorem inventory, proof path or finite-domain interpretation. Native short/sufficient row variants are provenance of the same assertion.')
def encode(case):
    spec=case['spec'];sy=Symbols(spec['theory']);entries=[dict(name='a'+str(i),role='axiom',original_name=n,formula=f) for i,(n,f) in enumerate(sorted(spec['theory']['axioms'].items()))]
    entries.append(dict(name='goal',role='conjecture',original_name='unchanged target',formula=spec['target']))
    text='% Exact signature and four explicit axioms; no library or proof path.\n'+'\n'.join('fof('+e['name']+','+e['role']+','+sy.formula(e['formula'])+').' for e in entries)+'\n'
    mapping=dict(case=case['group'],lane='theory-only',functions=sy.functions,predicates=sy.predicates,function_arities={sy.functions[n]:a for n,a in spec['theory']['functions'].items()},predicate_arities={sy.predicates[n]:a for n,a in spec['theory']['predicates'].items()},entries=entries,native_row_boundaries=[v['length'] for v in case['native_variants']],external_row_boundary=None)
    return text,mapping
