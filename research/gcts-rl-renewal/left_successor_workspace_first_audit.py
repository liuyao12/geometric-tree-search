"""Independent preservation/replay of the initial tree-estimation unknown."""
import gzip,hashlib,json,time
from pathlib import Path
import audit_tree_kernel as T
from audit_certificate_boundary import initial_for,pin
from audit_proof_boundary import expected_constructor,PINNED_MICRO,PINNED_PROGRAM

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/left-successor-20261011';OUT=PARENT/'workspace-study'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'first-unknown-audit-plan.json').read_text());producer=json.loads((OUT/'plan.json').read_text());micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and pin(boundary['program'])==PINNED_PROGRAM,'fixed authority')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'first unknown auditor source '+p)
    obs=load(OUT/'preflight.json.gz');need(len(obs)==1,'initial first-query unknown only');o=obs[0];rec=load(PARENT/'forward-control/native.json.gz')[0];initial=initial_for(micro,boundary['cases'][0]['initial'],rec['request']);nodes,root=expected_constructor(micro,initial,rec['request']);working=[];validate=T.validate_heap
    def observe(ns):validate(ns);working.append(ns)
    T.validate_heap=observe
    try:r=T.replay(boundary['program'],dict(nodes=nodes,node=root),producer['ceilings']['tree_steps'],producer['ceilings']['tree_heap_nodes'],keep=0)
    finally:T.validate_heap=validate
    need(r=={k:v for k,v in o['tree_result'].items() if k!='seconds'} and r['status']=='unknown_step_budget' and r['steps']==2000000 and [list(n) for n in working[0]]==o['final_tree_nodes'],'entire exact first unknown instruction/heap replay');required=sum((257+i).bit_length()+max(1,a.bit_length())+max(1,b.bit_length())+3 for i,(a,b) in enumerate(working[0]))+2;need(required==o['required_heap_capacity'],'partial-heap capacity is only a lower bound')
    result=dict(status='passed_first_workspace_estimation_unknown_replay',seconds=time.perf_counter()-began,native_queries=0,query=0,tree_status=r['status'],tree_steps=r['steps'],event_sha256=r['event_sha256'],partial_heap_required_cells_lower_bound=required,producer_query_checkpoint_seconds=o['preflight_seconds'],producer_total_seconds=None,scope='Original 2-million-tree-instruction cutoff reproduced exactly. The saved required_heap_capacity field is a partial-heap lower bound, not sufficient completion capacity. Initial producer total elapsed/peakRSS were not checkpointed on its terminal exception and remain unknown. Initial encoding auditor refused the incomplete preflight; no native execution occurred.')
    (OUT/'first-unknown-audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
