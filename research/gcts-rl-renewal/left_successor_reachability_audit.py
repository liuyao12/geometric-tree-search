"""Independent full-edge replay of the finite-grammar pruning certificate.

Uses a priority worklist over prerequisite counters, rather than producer
synchronous rounds. No reachability, catalog, compaction, model or solver
producer is imported. All unresolved interfaces participate identically.
"""
import collections,gc,gzip,hashlib,heapq,json,resource,time
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011'
def packed(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def worklist(edges,size):
    consumers=collections.defaultdict(list);remaining=[];maximum=[-1]*len(edges);queue=[];ranks=[None]*size
    for j,e in enumerate(edges):
        ins=set(e['inputs']);remaining.append(len(ins))
        for i in ins:consumers[i].append(j)
        if not ins:heapq.heappush(queue,(0,e['output']))
    while queue:
        rank,i=heapq.heappop(queue)
        if ranks[i] is not None:continue
        ranks[i]=rank
        for j in consumers[i]:
            remaining[j]-=1;maximum[j]=max(maximum[j],rank)
            if remaining[j]==0:heapq.heappush(queue,(maximum[j]+1,edges[j]['output']))
    return ranks
def main():
    began=time.perf_counter();plan=json.loads((OUT/'reachability-audit-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'reachability-summary.json').read_text());need(summary['native_queries']==summary['target_searches']==0,'preparation only')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen audit source '+p)
    result=dict(status='checking',native_queries=0,target_searches=0,variants=[])
    for lane in base['variants']:
        c=load(OUT/(lane+'-compact-core.json.gz'));w=load(OUT/(lane+'-reachability.json.gz'));pruned=load(OUT/(lane+'-reachable-core.json.gz'));words={packed(f):i for i,f in enumerate(c['basis'])};need(len(words)==len(c['basis']),'complete unique formula identities');edges=[dict(rule=j,inputs=[words[packed(f)] for f in r['premises']],output=words[packed(r['conclusion'])]) for j,r in enumerate(c['rules'])];ranks=worklist(edges,len(words));need(ranks==w['formula_ranks'],'complete independent least fixed-point minimal ranks');layers=[[i for i,r in enumerate(ranks) if r==j] for j in range(max(r for r in ranks if r is not None)+1)];need(layers==w['layers'] and len(layers)-1==w['rounds'],'all fixed-point layers')
        kept=[];removed=[]
        for e in edges:
            e['unreachable_inputs']=sorted(set(i for i in e['inputs'] if ranks[i] is None));e['eligible']=not e['unreachable_inputs'];(kept if e['eligible'] else removed).append(e['rule']);need(not e['eligible'] or ranks[e['output']] is not None,'closure under every edge, including native-unresolved ones')
        need(edges==w['edges'] and kept==w['retained_rules'] and removed==w['removed_rules'],'every hyperedge, eligibility and unreachable-premise witness');need(all(ranks[e['output']]==0 for e in edges if not e['inputs']),'all zero-input axiom/tautology/reflexivity/derived roots retained')
        need(w['full_core_sha256']==hashlib.sha256((OUT/(lane+'-compact-core.json.gz')).read_bytes()).hexdigest() and w['basis_sha256']==hashlib.sha256(packed(c['basis'])).hexdigest() and w['rules_sha256']==hashlib.sha256(packed(c['rules'])).hexdigest(),'full grammar provenance hashes');need(pruned['rules']==[c['rules'][j] for j in kept] and pruned['structural_pruning']['full_rule_ids']==kept and pruned['structural_pruning']['witness_sha256']==hashlib.sha256((OUT/(lane+'-reachability.json.gz')).read_bytes()).hexdigest(),'exact all-alternative rule projection');names={r['command']['name'] for r in pruned['rules'] if r['command']['rule']=='block'};need(pruned['definitions']==[d for d in c['definitions'] if d['name'] in names],'exact full retained definition inventory');need({k:v for k,v in c.items() if k not in ('rules','definitions')}=={k:v for k,v in pruned.items() if k not in ('rules','definitions','structural_pruning')},'syntax, target, theory, scope and all conditional contexts unchanged')
        result['variants'].append(dict(lane=lane,full_edges=len(edges),retained_edges=len(kept),removed_edges=len(removed),reachable_formulas=sum(r is not None for r in ranks),all_unreachable_rules_have_an_explicit_unreachable_premise=True,all_full_zero_input_roots_retained=True,all_full_edges_participated=True,retained_definitions=len(pruned['definitions'])));(OUT/'reachability-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('independent reachability',lane,len(kept),'retained',flush=True);del c,w,pruned,words,edges,ranks,layers;gc.collect()
        if time.perf_counter()-began>plan['ceilings']['seconds']:raise TimeoutError('unknown_reachability_audit_time_budget')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>plan['ceilings']['rss_bytes']:raise MemoryError('unknown_reachability_audit_memory_budget')
    result.update(status='passed_finite_grammar_structural_pruning',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,safety='Induct over strict-prior finite proof positions: zero-input outputs belong to the fixed point; every later output follows an included full edge with earlier reachable inputs. Every removed edge has an input outside this closed set, hence cannot occur in any full-grammar word. All retained alternatives remain. This is structural pruning of the declared finite grammar, not full-FOL nonprovability or native authority.')
    (OUT/'reachability-audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
