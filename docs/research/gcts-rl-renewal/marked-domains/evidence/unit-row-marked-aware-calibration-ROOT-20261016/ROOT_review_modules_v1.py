"""Root Source-only reviews of frozen marked-aware modules. No model imports."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def checked(r):
    p=Path(r['path']);assert p==p.resolve()and pin(p)==r
    return p
def save(name,v):
    p=HERE/name
    with p.open('x')as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)
def main():
    parent=checked(dict(path=str(BASE/'unit-row-parallel-fibres-report-ROOT-20261016/ROOT-progress-checkpoint-v1.json'),sha256='c0183654f78fe13100360f920b1cc03557daf600f3ad787305a89f127f928423',bytes=26662))
    authority=read(parent)
    result={}
    for role,folder,want in [
       ('proposer','unit-row-marked-aware-fibre-proposer-source-20261016','977a877f898d3fb9f9aa85a9b4d2343467996ef15849d0c733672905bea1e35c'),
       ('checker','unit-row-marked-aware-fibre-checker-source-20261016','5d3e7854b3eff9a01a673b1cee12fb71b9d60d59b45efe6ec0578549dc4b8c9a')]:
        cr=pin(BASE/folder/'Source-contract-v1.json');assert cr['sha256']==want
        c=read(checked(cr))
        for key in ('sources','original_model_sources','original_model_inputs'):
            for ref in c[key].values():checked(ref)
        assert c['original_model_sources']==authority['original_model_sources']
        assert c['original_model_binding']==authority['original_model_binding']
        raw=checked(c['source']).read_bytes();t=ast.parse(raw);compile(t,c['source']['path'],'exec')
        assert not any(isinstance(n,(ast.Import,ast.ImportFrom))and any(a.name not in('hashlib','json')for a in n.names)for n in t.body)
        assert not any(isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)for n in t.body)
        rr=dict(c['Review_ABI'])
        rr.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,
            scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],whole_current_Source_and_contract_read=True,
            exact_current_sources_and_original_authority_verified=True,AST_compile_only=True,
            authorship_disclosure='Root authors metadata/experimental coordination, neither of these scientific modules. Whole code read in previous turn and exact bytes reauthenticated; whole current contracts read this turn. Shared c354 membership/point primitives are explicit; separate enumeration is not an unrelated second mathematics kernel.',
            checks=[
               'Assigned nonimp scope matches all six original rules: AX/indexedGamma/UG/orderedMP; UI and EqSubst always output implication.',
               'Both-missing full original grammar uses derived43-output-size bound; repeated-read occurs-empty explicitly accounted. No target/carrier restriction or termbound change.',
               'Full current original/marked states, identity/ordered ports/exclusions/remote marks/collision ledgers remain authoritative; absence differs from zero and pending reads are not facts.',
               'Only fully marked legal distinct packets count before missing-prefix TWO lower-bound stop; complete0/1 requires all fibres independently finished; allassigned completeMANY retained.',
               'New typed provenance never fabricates old c354 receipt or engine11 compatibility. Partial hashes/counters/cursor EOF supply no completion authority.',
               'Callbacks/authority/membership resources propagate; no timing/fit/result/gain/graph/proof/RL claim from Source review. Runtime calibration and explicit future engine integration still required.'])
        result[role]=save('ROOT-'+role+'-Source-review-v1.json',rr)
    save('ROOT-module-review-concordance-v1.json',dict(parent=pin(parent),reviews=result,scientific_calls=0,previous_goal_turn='progress'))
    print(json.dumps(result))
if __name__=='__main__':main()

