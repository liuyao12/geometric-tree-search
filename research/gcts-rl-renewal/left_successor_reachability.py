"""Target-blind proved structural pruning of a complete finite grammar.

All templates, including native-unresolved ones, participate in the closure.
Conditional premises remain whole explicit formulas. The fixed point supplies
no selected proof path. It removes only templates with an unreachable premise;
strict-prior finite proof positions prove such templates cannot occur in any
full-grammar proof word. This is not unrestricted FOL nonprovability.
"""
import collections,gc,gzip,hashlib,json,resource,time
from pathlib import Path
from certificate_boundary_search import canonical
from left_successor_catalog import prospective_points

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011'
def need(t,m):
    if not t:raise ValueError(m)
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def closure(rules,basis):
    words={canonical(f):i for i,f in enumerate(basis)};edges=[dict(rule=j,inputs=[words[canonical(f)] for f in r['premises']],output=words[canonical(r['conclusion'])]) for j,r in enumerate(rules)];rank={e['output']:0 for e in edges if not e['inputs']};layers=[sorted(rank)];rounds=0
    while True:
        additions={e['output'] for e in edges if e['output'] not in rank and all(i in rank for i in e['inputs'])}
        if not additions:break
        rounds+=1;rank.update({i:rounds for i in additions});layers.append(sorted(additions))
    kept=[];removed=[]
    for e in edges:
        e['unreachable_inputs']=sorted(set(i for i in e['inputs'] if i not in rank));e['eligible']=not e['unreachable_inputs'];(kept if e['eligible'] else removed).append(e['rule'])
    return dict(formula_ranks=[rank.get(i) for i in range(len(basis))],layers=layers,edges=edges,retained_rules=kept,removed_rules=removed,rounds=rounds)
def fixtures():
    f=lambda x:['pred',x,[]];r=lambda ins,out:dict(premises=list(map(f,ins)),conclusion=f(out));basis=list(map(f,['a','b','c','d']))
    c=closure([r([],'a'),r(['a'],'b'),r(['b'],'a'),r(['c'],'d'),r(['d'],'c'),r(['a','c'],'b')],basis);need(c['formula_ranks']==[0,1,None,None] and c['retained_rules']==[0,1,2],'rooted closure excludes unseeded cycles and any unreachable input')
    c=closure([r([],'a'),r([],'c'),r(['a'],'b'),r(['c'],'b'),r(['b'],'d')],basis);need(c['retained_rules']==[0,1,2,3,4] and c['formula_ranks']==[0,1,0,2],'all alternatives retained; no chosen path')
def main():
    began=time.perf_counter();plan=json.loads((OUT/'reachability-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());need(json.loads((OUT/'audit.json').read_text())['status']=='passed_preparation_audit_only','full grammar audit');need(json.loads((OUT/'compaction-preparation-audit.json').read_text())['status']=='passed_compaction_preparation_audit_only','all exact compact proof bytes audited')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen reachability source '+p)
    fixtures();summary=dict(status='preparing',native_queries=0,target_searches=0,variants=[])
    for lane in base['variants']:
        c=load(OUT/(lane+'-compact-core.json.gz'));start=time.perf_counter();w=closure(c['rules'],c['basis']);w.update(lane=lane,full_core_sha256=hashlib.sha256((OUT/(lane+'-compact-core.json.gz')).read_bytes()).hexdigest(),basis_sha256=hashlib.sha256(canonical(c['basis'])).hexdigest(),rules_sha256=hashlib.sha256(canonical(c['rules'])).hexdigest(),scope='Every full-grammar edge participates, including native-unadmitted templates. Ranks are complete least fixed-point layers; retained edges include every alternative with reachable inputs. No chosen target proof path.');save(OUT/(lane+'-reachability.json.gz'),w);full_rules=c['rules'];full_definitions=c['definitions'];c['rules']=[full_rules[i] for i in w['retained_rules']];names={r['command']['name'] for r in c['rules'] if r['command']['rule']=='block'};c['definitions']=[d for d in full_definitions if d['name'] in names];c['structural_pruning']=dict(full_rule_ids=w['retained_rules'],witness_sha256=hashlib.sha256((OUT/(lane+'-reachability.json.gz')).read_bytes()).hexdigest(),scope='Proved structural pruning of this complete finite grammar. Every accepted finite strict-prior proof word is retained. Not a full-FOL nonprovability claim.');save(OUT/(lane+'-reachable-core.json.gz'),c);counts=collections.Counter(r['description']['operation'] for r in c['rules']);stats=dict(lane=lane,full_formulas=len(w['formula_ranks']),reachable_formulas=sum(q is not None for q in w['formula_ranks']),rounds=w['rounds'],full_interfaces=len(full_rules),retained_interfaces=len(c['rules']),removed_interfaces=len(w['removed_rules']),full_definitions=len(full_definitions),retained_definitions=len(c['definitions']),retained_local_commands=sum(len(d['proof']) for d in c['definitions']),retained_max_commands=max(len(d['proof']) for d in c['definitions']),retained_operation_counts=dict(counts),point_counts=[prospective_points(c,n) for n in base['prospective_lengths']],closure_and_export_seconds=time.perf_counter()-start);summary['variants'].append(stats);(OUT/'reachability-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(stats),flush=True);del c,w,full_rules,full_definitions;gc.collect()
        if time.perf_counter()-began>plan['ceilings']['seconds']:raise TimeoutError('unknown_reachability_preparation_time_budget')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>plan['ceilings']['rss_bytes']:raise MemoryError('unknown_reachability_preparation_memory_budget')
    summary.update(status='prepared_fixed_point_not_yet_independently_audited',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,native_authority='not established; all retained local definitions must be natively admitted before a model exists');(OUT/'reachability-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
