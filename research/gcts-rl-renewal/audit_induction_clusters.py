"""Independent proof-motif provenance, complete instances, graph and AC replay.

No miner, generator, point model, graph, search or producer imports. Historical
independent proof/resource auditors provide the serialized primitive checker.
"""
import collections,hashlib,itertools,json,time
from pathlib import Path
import audit_induction_proofs as I
import audit_semantic_proofs as A
from audit_serialized_kernel import freeze
from audit_proof_compaction import native_binding
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
MEASURED_SOURCES=('induction_proof_catalogs.py','induction_proof_problems.py','induction_proof_tiles.py','run_induction_proofs.py','audit_induction_proofs.py','test_induction_proofs.py','coarse_proof_tiles.py','audit_coarse_proofs.py','audit_proof_policy.py','audit_proof_clusters.py','audit_semantic_proofs.py','audit_serialized_kernel.py','audit_proof_compaction.py','audit_tree_kernel.py','proof_clusters.py','semantic_proof_tiles.py','semantic_proof_catalogs.py','semantic_proof_problems.py','run_semantic_proofs.py','proof_block_search.py','turtle.py','logic.py','kernel_machine.py','serialized_kernel.py','tree_kernel.py','tree_machine.py','fol_checker.tree','tree_native.py','tree_runner.cpp','induction_clusters.py','audit_induction_clusters.py','run_induction_clusters.py','test_induction_clusters.py','run_induction_cluster_tests.py')
def sha(a):return I.sha(a)
def family(r):
    p=r['recipe']
    if p['kind']=='copy':return dict(kind='copy')
    if p['kind']=='primitive':return dict(kind='primitive',operation=p['witness']['rule'])
    out=dict(kind='block',operation=p['operation'])
    if p['operation'].endswith('rewrite'):out.update(axiom=p['axiom'],direction=p['move']['direction'])
    return out
def learned(c,r,p):
    keys=tuple(sorted(r['placements']));out=[]
    for size in (2,3):
        for group in itertools.combinations(keys,size):
            slots={k[0] for k in group};adj={i:set() for i in slots}
            for slot,rule,refs in group:
                for ref in refs:
                    if ref in slots:adj[slot].add(ref);adj[ref].add(slot)
            seen=set();queue=[group[0][0]]
            while queue:
                x=queue.pop()
                if x not in seen:seen.add(x);queue.extend(adj[x]-seen)
            if seen!=slots:continue
            origin=min(slots);nodes=[dict(offset=slot-origin,family=family(c['rules'][rule]),refs=[j-origin for j in refs]) for slot,rule,refs in group]
            out.append(dict(name='induction-motif-'+sha(nodes)[:20],nodes=nodes,span=max(slots)-origin+1,size=size,sources=[dict(problem=p['id'],certificate_sha256=sha(r['decoded']['request']),members=group,origin=origin)]))
    return out
def merged(rows):
    out={}
    for items in rows:
        for t in items:
            if t['name'] not in out:out[t['name']]=t
            else:
                A.need(out[t['name']]['nodes']==t['nodes'],'pattern collision')
                for source in t['sources']:
                    if source not in out[t['name']]['sources']:out[t['name']]['sources'].append(source)
    return [out[k] for k in sorted(out)]
def instances(c,n,library):
    # Exact relational joins of independently enumerated original candidates.
    # Hash the shared formula-port columns at each join; this is the exhaustive
    # Cartesian relation filtered by equality, without materializing failures.
    universe=A.candidates(c,n);out={}
    for pattern in library:
        buckets=[[rid for rid,r in enumerate(c['rules']) if sha(family(r))==sha(node['family'])] for node in pattern['nodes']]
        for start in range(n-pattern['span']+1):
            joined=[((),{})];columns=set()
            for node,bucket in zip(pattern['nodes'],buckets):
                relation=[]
                for rid in bucket:
                    key=(start+node['offset'],rid,tuple(start+j for j in node['refs']))
                    if key in universe:relation.append((key,universe[key]))
                if not relation:joined=[];break
                new_columns=set(relation[0][1]);shared=tuple(sorted(columns&new_columns));index=collections.defaultdict(list)
                for key,ports in relation:
                    A.need(set(ports)==new_columns,'fixed relation port columns')
                    index[tuple(ports[p] for p in shared)].append((key,ports))
                following=[]
                for members,ports in joined:
                    for key,new_ports in index[tuple(ports[p] for p in shared)]:
                        following.append((members+(key,),ports|new_ports))
                joined=following;columns.update(new_columns)
                if not joined:break
            for members,ports in joined:
                if members not in out:out[members]=dict(members=members,patterns=[],start=start)
                out[members]['patterns'].append(pattern['name'])
    return [out[k] for k in sorted(out)]

class Points(I.Points):
    def __init__(self,c,n,library=(),marked=True):
        super().__init__(c,n,'support' if marked else 'none');self.instances=instances(c,n,library);lookup={t['members'][0]:cid for cid,t in enumerate(self.tiles)}
        for item in self.instances:
            cid=len(self.tiles);weights=collections.Counter();marks={}
            for k in item['members']:
                t=self.tiles[lookup[k]];weights.update(t['weights'])
                for p,v in t['marks'].items():
                    if p[1]==2:continue
                    A.need(p not in marks or marks[p]==v,'aggregate motif marks');marks[p]=v
                marks[(2*k[0],2)]=cid
            A.need(all(v==12 for v in weights.values()),'distinct capacity cells')
            self.tiles.append(dict(members=item['members'],item=item,weights=dict(weights),marks=marks))
    def rank(self,cid):
        t=self.tiles[cid];return (0 if t['item'] else 1,-int(any(k[0]==self.n-1 for k in t['members'])) if t['item'] else 0,-len(t['members']),cid)

def point_run(c,n,r,library):
    points=Points(c,n,library,r['marked']);A.need(r['base_universe']==len(points.base) and r['candidate_universe']==len(points.tiles) and r['motif_instances']==len(points.instances) and r['library_sha256']==sha(library),'whole primitive and motif inventory')
    if r['marked']:I.support_certificate(c,r['support_certificate'])
    else:A.need(r['support_certificate'] is None,'unmarked control')
    initial=points.domains([]);stats=dict(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,tile_attempts=0,macro_attempts=0);best=[];leaf=None;cuts=0
    peaks=[n,len(set().union(*initial.values())),sum(map(len,initial.values()))]
    def visit(tree,ids):
        nonlocal best,leaf,cuts
        stats['nodes']+=1;A.need(tree['selected']==tuple(ids),'actual motif prefix');ds=points.domains(ids)
        if tree['kind']=='cutoff':A.need(set(tree)=={'kind','selected','cutoff'} and tree['cutoff']=='wall_entry' and r['seconds']>=r['limits']['seconds'],'entry wall');cuts+=1;return None
        kind,p,choices=points.decision(ds);A.need(tree['kind']==kind and tree['point']==p,'global dead/forced/generation order')
        candidates=set().union(*ds.values()) if ds else set();edges={cid:tuple(sorted(p for p,values in ds.items() if cid in values)) for cid in candidates}
        A.need(tree['graph_sha256']==sha((tuple(sorted((p,tuple(sorted(v))) for p,v in ds.items())),tuple(sorted(edges.items())))),'every complete motif graph')
        peaks[1]=max(peaks[1],len(candidates));peaks[2]=max(peaks[2],sum(map(len,ds.values())))
        if kind=='dead':A.need('children' not in tree and 'cutoff' not in tree,'closed dead leaf');return False
        if len(points.expand(ids))>len(points.expand(best)):best=list(ids)
        if kind=='empty':A.need('children' not in tree and 'cutoff' not in tree,'closed solution leaf');leaf=list(ids);return True
        stats['forced' if kind=='forced' else 'branches']+=1;children=tree['children'];A.need(tuple(x['candidate'] for x in children)==tuple(choices[:len(children)]),'every executed ordering prefix')
        for j,child in enumerate(children):
            cid=child['candidate'];cost=len(points.tiles[cid]['members']);stats['base_attempts']+=cost;stats['tile_attempts']+=1;stats['macro_attempts']+=int(cost>1)
            ok=visit(child['tree'],ids+[cid])
            if ok is not False:A.need(j==len(children)-1 and 'cutoff' not in tree,'stop at open/successful child');return ok
            stats['backtracks']+=1
        if 'cutoff' in tree:
            A.need(len(children)<len(choices),'open unexecuted suffix');reason=tree['cutoff'];A.need(reason in ('wall_before_candidate','attempts_before_candidate'),'declared cutoff')
            A.need(r['seconds']>=r['limits']['seconds'] if reason.startswith('wall') else stats['base_attempts']+len(points.tiles[choices[len(children)]]['members'])>r['limits']['base_attempts'],'actual budget');cuts+=1;return None
        A.need(len(children)==len(choices),'all closed branches covered');return False
    ok=visit(r['search_tree'] if r['search_tree'] is not None else r['partial_tree'],[])
    expected='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope';A.need(r['status']==expected and cuts==int(ok is None),'tri-state result')
    A.need((r['search_tree'] is None)==(ok is None) and (r['partial_tree'] is None)==(ok is not None),'complete/open distinction')
    A.need(all(r[k]==v for k,v in stats.items()) and stats['base_attempts']<=r['limits']['base_attempts'],'all expanded attempts and backtracks')
    selected=leaf if ok else best;A.need(r['selected']==tuple(selected) and r['placements']==points.expand(selected),'exact motif expansion');A.need(r['tile_generations']==(1,)*len(selected),'generation-zero roots')
    A.need((r['peak_frontier_points'],r['peak_candidate_nodes'],r['peak_incidences'])==tuple(peaks),'complete graph peaks');A.domains(points.base,n,c['target_id'],r['placements'])
    if ok:
        expected=tuple(dict(candidate=cid,members=points.tiles[cid]['members'],item=points.tiles[cid]['item']) for cid in selected if points.tiles[cid]['item'])
        A.need(r['solution_motifs']==freeze(list(expected)),'only actually placed motifs');proof=A.check_decoded(c,n,r)
    else:A.need('decoded' not in r,'no proof at cutoff');proof=None
    return dict(**stats,cutoffs=cuts,exact_solution=ok is True,proof=proof)

def provenance(rows,library):
    reconstructed=[]
    for row in rows:
        r=row['run']['result']
        A.need(r['status']=='finite_exact_proof_tiling','only complete donor proofs may teach motifs')
        patterns=learned(row['catalog'],r,row['problem'])
        A.need(freeze(patterns)==row['mined'],'every connected two/three-cell source fragment')
        reconstructed.append(patterns)
    expected=merged(reconstructed)
    A.need(freeze(expected)==library,'entire learned library and source certificate provenance')
    return dict(patterns=len(expected),source_occurrences=sum(len(p['sources']) for p in expected))

def audit(path=DOCS/'induction-clusters-001.json'):
    path=Path(path);raw=json.loads(path.read_text());d=freeze(raw);began=time.perf_counter()
    A.need(set(d['sources'])==set(MEASURED_SOURCES),'whole measured dependency/source set')
    for name,pin in d['sources'].items():A.need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==pin,'frozen measured source '+name)
    code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program']
    A.need(d['program_sha256']==sha(code) and d['initial_library']==() and d['policy'] is None,'fixed checker and no imported proof/library/policy')
    lanes=('gcts-base','gcts-motifs','csp-base','csp-motifs')
    A.need(d['configuration']==dict(seconds=20,donor_seconds=20,base_attempts=50000,native_steps=100000000,replicas=2,lanes=lanes,motif_sizes=(2,3),marked=True),'fixed matched experiment')
    external=I.external_cases();donor_ids=('ind-add-left-zero','ind-add-left-one')
    A.need(tuple(x['problem']['id'] for x in d['donors'])==donor_ids,'two fresh source statements')
    donors=[];source_reports=[]
    def bound(row):
        p=row['problem'];c=row['catalog'];A.need({k:p[k] for k in external[p['id']]}==external[p['id']],'independent external statement/bounds')
        A.need(c['theory']==p['theory'] and c['target']==p['target'] and c['configuration']['term_bound']==p['term_bound'] and c['configuration']['enable_induction']==p['enable_induction'] and sha(c)==row['catalog_sha256'],'entire goal-derived grammar binding')
        return I.inventory(c)
    for descriptor in raw['donors']:
        A.need(descriptor['file']=='induction-cluster-donors-001/'+descriptor['problem']['id']+'.json.gz','immutable donor shard')
        row=freeze(I.load_case(descriptor));language=bound(row);run=row['run'];r=run['result']
        A.need(run['catalog_sha256']==row['catalog_sha256'] and r['marking']=='support' and r['limits']==dict(seconds=20,base_attempts=50000),'fresh donor lane and budget')
        report=I.point_run(row['catalog'],row['problem']['length'],r)
        A.need(report['exact_solution'] and run['native']['status']=='accepted','complete checked source proof')
        native_binding(code,json.loads(A.packed(r['decoded']['request'])),json.loads(A.packed(run['native'])))
        donors.append(row);source_reports.append(dict(id=row['problem']['id'],inventory=language,report=report))
        print('audited donor',row['problem']['id'],flush=True)
    library=provenance(donors,d['library']);A.need(d['library_sha256']==sha(d['library']),'frozen learned library')
    evaluation_ids=('ind-mul-left-zero','ind-add-left-successor','ind-no-schema','ind-too-short','ind-wrong-target')
    A.need(tuple(x['problem']['id'] for x in d['cases'])==evaluation_ids,'all nominated transfer and negative controls')
    reports=[]
    for i,descriptor in enumerate(raw['cases']):
        A.need(descriptor['file']=='induction-cluster-cases-001/'+descriptor['problem']['id']+'.json.gz','immutable full evaluation shard')
        row=freeze(I.load_case(descriptor));language=bound(row);p=row['problem'];c=row['catalog'];runs=[]
        order=[]
        for replica in range(2):
            shift=(i+replica)%4;order.extend((replica,lane) for lane in lanes[shift:]+lanes[:shift])
        A.need(tuple((r['replica'],r['lane']) for r in row['runs'])==tuple(order),'all eight runs in rotating replica order')
        for run in row['runs']:
            r=run['result'];active=d['library'] if run['lane'].endswith('motifs') else ()
            A.need(run['catalog_sha256']==row['catalog_sha256'] and r['limits']==dict(seconds=20,base_attempts=50000) and r['marked'] is True,'same complete catalog, support constraints and finite limits')
            report=(csp_run if run['lane'].startswith('csp') else point_run)(c,p['length'],r,active)
            if r['status']=='finite_exact_proof_tiling':
                A.need(run['native']['status']=='accepted','complete native acceptance')
                native_binding(code,json.loads(A.packed(r['decoded']['request'])),json.loads(A.packed(run['native'])))
                report['native_status']='accepted'
            else:A.need('native' not in run,'no acceptance on exhaustion or cutoff')
            runs.append(dict(replica=run['replica'],lane=run['lane'],report=report))
        reports.append(dict(id=p['id'],inventory=language,runs=runs));print('audited evaluation',p['id'],flush=True)
    result=dict(status='passed',seconds=time.perf_counter()-began,donors=source_reports,library=library,cases=reports,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      scope='Independent complete source/recipient grammars and primitive expansions; every connected mined fragment with exact certificate provenance; complete family/geometry instances by relational joins; every point graph, scheduling decision, macro expansion, remote resource constraint and classical support deletion; all complete/open prefixes, budgets, base fallback, witness and native bindings. Compiler/native implementation remain trusted. Atomic motifs preserve solution sets rather than the original primitive scheduling trace.')
    raw['independent_audit']=result;path.write_text(json.dumps(raw,separators=(',',':'))+'\n');return result

def csp_run(c,n,r,library):
    points=I.Points(c,n,'support' if r['marked'] else 'none');universe=points.base;keys=[sorted(k for k in universe if k[0]==i) for i in range(n)];maps=[[universe[k] for k in row] for row in keys]
    full=[(1<<len(row))-1 for row in keys];index=[]
    for row in maps:
        present={};values={}
        for k,m in enumerate(row):
            for p,v in m.items():present[p]=present.get(p,0)|(1<<k);values[p,v]=values.get((p,v),0)|(1<<k)
        index.append((present,values))
    def support(i,k,j):
        mask=full[j];present,values=index[j]
        for p,v in maps[i][k].items():mask&=(full[j]^present.get(p,0))|values.get((p,v),0)
        return mask
    if r['marked']:I.support_certificate(c,r['support_certificate'])
    else:A.need(r['support_certificate'] is None,'unmarked classical control')
    initial_candidates=set().union(*points.domains([]).values());cid={t['members'][0]:i for i,t in enumerate(points.tiles)}
    initial=[sum(1<<j for j,k in enumerate(row) if cid[k] in initial_candidates) for row in keys]
    motifs=instances(c,n,library);lookup={key:(i,j) for i,row in enumerate(keys) for j,key in enumerate(row)};assignments=[tuple(lookup[k] for k in item['members']) for item in motifs]
    A.need(r['motif_instances']==len(motifs) and r['base_universe']==len(universe) and r['candidate_universe']==len(universe) and r['library_sha256']==sha(library),'same complete classical envelope and motifs')
    stats=dict(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,macro_attempts=0,support_tests=0,removed_values=0,revisions=0);leaf=None;used=None;cuts=0
    def visit(t,incoming,path):
        nonlocal leaf,used,cuts
        stats['nodes']+=1;A.need(t['incoming']==tuple(hex(x) for x in incoming),'exact incoming classical domains');ds=list(incoming)
        queue=collections.deque((i,j) for i in range(n) for j in range(n) if i!=j)
        if not all(ds):A.need(t['kind']=='dead' and not t['revisions'] and not t['children'] and 'cutoff' not in t and t['domains']==tuple(hex(x) for x in ds),'initial dead domain');return False
        for revision,(i,j,removed) in enumerate(t['revisions']):
            A.need(queue and queue.popleft()==(i,j),'actual AC queue');expected=0
            for k in I.B.bits(ds[i]):
                stats['support_tests']+=1
                if not support(i,k,j)&ds[j]:expected|=1<<k
            A.need(removed==hex(expected),'every independently reconstructed support deletion');stats['revisions']+=1;stats['removed_values']+=I.B.count(expected);ds[i]&=~expected
            if not ds[i]:A.need(revision==len(t['revisions'])-1 and not t['children'] and 'cutoff' not in t and t['kind']=='dead' and t['domains']==tuple(hex(x) for x in ds),'dead after propagation');return False
            if expected:queue.extend((k,i) for k in range(n) if k!=i and k!=j)
        A.need(t['domains']==tuple(hex(x) for x in ds),'complete exported classical domains')
        if queue:A.need(t['kind']=='ac' and not t['children'] and t['cutoff']=='wall_ac' and r['seconds']>=r['limits']['seconds'],'only wall may leave AC queue open');cuts+=1;return None
        if all(I.B.count(x)==1 for x in ds):A.need(t['kind']=='empty' and not t['children'] and 'cutoff' not in t,'classical singleton witness');leaf=tuple(keys[i][next(I.B.bits(mask))] for i,mask in enumerate(ds));used=tuple(path);return True
        i=min((i for i in range(n) if I.B.count(ds[i])>1),key=lambda i:(I.B.count(ds[i]),i));A.need(t['kind']=='branch' and t['slot']==i,'classical MRV');stats['branches']+=1
        offered=[mid for mid,ass in enumerate(assignments) if any(j==i for j,k in ass) and all(ds[j]&(1<<k) for j,k in ass)]
        offered.sort(key=lambda mid:(-int(any(k[0]==n-1 for k in motifs[mid]['members'])),-len(motifs[mid]['members']),mid))
        choices=[('motif',mid,assignments[mid]) for mid in offered]+[('base',k,((i,k),)) for k in I.B.bits(ds[i])];children=t['children']
        A.need(tuple((x['mode'],x['choice']) for x in children)==tuple((a,b) for a,b,ass in choices[:len(children)]),'complete macro plus base fallback ordering prefix')
        for j,child in enumerate(children):
            mode,choice,ass=choices[j];stats['base_attempts']+=len(ass);stats['macro_attempts']+=int(mode=='motif');following=list(ds)
            for p,v in ass:following[p]=1<<v
            ok=visit(child['tree'],following,path+([choice] if mode=='motif' else []))
            if ok is not False:A.need(j==len(children)-1 and 'cutoff' not in t,'stop at open/successful child');return ok
            stats['backtracks']+=1
        if 'cutoff' in t:
            A.need(len(children)<len(choices),'remaining classical suffix');reason=t['cutoff'];A.need(reason in ('wall_before_candidate','attempts_before_candidate'),'classical cutoff')
            A.need(r['seconds']>=r['limits']['seconds'] if reason.startswith('wall') else stats['base_attempts']+len(choices[len(children)][2])>r['limits']['base_attempts'],'actual classical budget');cuts+=1;return None
        A.need(len(children)==len(choices),'closed classical search covers all choices');return False
    ok=visit(r['search_tree'] if r['search_tree'] is not None else r['partial_tree'],initial,[])
    expected='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope';A.need(r['status']==expected and cuts==int(ok is None),'classical tri-state outcome')
    A.need((r['search_tree'] is None)==(ok is None) and (r['partial_tree'] is None)==(ok is not None),'classical complete/open distinction');A.need(all(r[k]==v for k,v in stats.items()) and stats['base_attempts']<=r['limits']['base_attempts'],'all classical work')
    if ok:A.need(r['placements']==leaf and r['used_motif_proposals']==used,'actual classical witness and proposal path');proof=A.check_decoded(c,n,r)
    else:A.need(r['placements']==() and 'decoded' not in r,'no classical witness at cutoff');proof=None
    return dict(**stats,cutoffs=cuts,exact_solution=ok is True,proof=proof)

if __name__=='__main__':print('passed',audit()['seconds'])
