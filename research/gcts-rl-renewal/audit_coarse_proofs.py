"""Independent finite inventory, coarse point search and classical AC replay.

No producer, graph, solver, miner or catalog-generator imports. All logical
proofs expand through the earlier independently implemented serialized checker.
"""
import collections,hashlib,json,time
from pathlib import Path
import audit_semantic_proofs as A
import audit_proof_clusters as G
import audit_proof_policy as B
from audit_serialized_kernel import freeze
from audit_proof_compaction import native_binding
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
LANES=('base','fine-meta','coarse2-base','coarse2-meta','coarse3-meta','csp')
def count(x):return bin(x).count('1')
def bits(x):
    while x:
        low=x&-x;yield low.bit_length()-1;x-=low

class Points:
    def __init__(self,c,n,width,library):
        self.n=n;self.target=c['target_id'];self.width=width;self.base=A.candidates(c,n)
        self.groups=tuple(tuple(range(i,min(i+width,n))) for i in range(0,n,width));where={slot:g for g,slots in enumerate(self.groups) for slot in slots}
        items,complete=G.index(c,n,library,1000000);A.need(complete,'complete independent macro enumeration');self.items=items;self.tiles=[];self.root={(2*g,0) for g in range(len(self.groups))}
        for members,item in [( (key,),None) for key in sorted(self.base)]+[(t['members'],t) for t in items]:
            cid=len(self.tiles);owned=set();weights=collections.Counter();marks={}
            for key in members:
                slot=key[0];A.need(slot not in owned,'distinct metatile constituents');owned.add(slot)
                weights[(2*where[slot],0)]+=12//len(self.groups[where[slot]])
                for j,v in self.base[key].items():
                    p=(2*j,1);A.need(p not in marks or marks[p]==v,'compatible internal formula ports');marks[p]=v
                marks[(2*slot,2)]=cid
            self.tiles.append(dict(weights=dict(weights),marks=marks,members=members,item=item))
    def expand(self,ids):return tuple(sorted((key for cid in ids for key in self.tiles[cid]['members']),key=lambda k:k[0]))
    def rank(self,cid):
        t=self.tiles[cid];item=t['item'];members=t['members']
        return (0 if item else 1,-int(any(k[0]==self.n-1 for k in members)) if item else 0,-len(members),-item['level'] if item else 0,G.sha(item) if item else '',cid)
    def domains(self,ids):
        totals=collections.Counter();marks={(2*(self.n-1),1):self.target};seen=set()
        for cid in ids:
            A.need(type(cid) is int and 0<=cid<len(self.tiles) and cid not in seen,'candidate identity');seen.add(cid);t=self.tiles[cid]
            for p,v in t['weights'].items():totals[p]+=v;A.need(totals[p]<=12,'exact coarse capacity')
            for p,v in t['marks'].items():A.need(p not in marks or marks[p]==v,'ownership and formula markings');marks[p]=v
        domains={p:set() for p in self.root if totals[p]<12}
        for cid,t in enumerate(self.tiles):
            if cid not in seen and all(totals[p]+v<=12 for p,v in t['weights'].items()) and all(p not in marks or marks[p]==v for p,v in t['marks'].items()):
                for p in t['weights'].keys()&domains.keys():domains[p].add(cid)
        return domains
    def decision(self,ds):
        dead=sorted(p for p,x in ds.items() if not x)
        if dead:return 'dead',dead[0],[]
        forced=sorted(p for p,x in ds.items() if len(x)==1)
        if forced:p=forced[0];return 'forced',p,sorted(ds[p],key=self.rank)
        if not ds:return 'empty',None,[]
        p=min(ds,key=lambda p:(len(ds[p]),p));return 'branch',p,sorted(ds[p],key=self.rank)

def point_run(c,n,r,library):
    points=Points(c,n,r['width'],library);A.need(r['groups']==points.groups and r['base_universe']==len(points.base) and r['candidate_universe']==len(points.tiles) and r['index_instances']==len(points.items),'whole contracted inventory and partition')
    initial=points.domains([]);initial_candidates=set().union(*initial.values()) if initial else set()
    stats=dict(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,tile_attempts=0);best=[];leaf=None;cuts=0;peaks=[len(points.root),len(initial_candidates),sum(map(len,initial.values()))]
    def visit(t,ids):
        nonlocal best,leaf,cuts
        stats['nodes']+=1;A.need(t['selected']==tuple(ids),'actual coarse prefix');ds=points.domains(ids)
        if t['kind']=='cutoff':
            A.need(t.get('cutoff')=='wall_entry' and r['seconds']>=r['limits']['seconds'],'entry wall cutoff');cuts+=1;return None
        kind,p,choices=points.decision(ds);A.need(t['kind']==kind and t['point']==p,'global dead/forced/generation decision')
        candidates=set().union(*ds.values()) if ds else set();peaks[1]=max(peaks[1],len(candidates));peaks[2]=max(peaks[2],sum(map(len,ds.values())))
        edges={cid:tuple(sorted(p for p,values in ds.items() if cid in values)) for cid in candidates};fingerprint=(tuple(sorted((p,tuple(sorted(values))) for p,values in ds.items())),tuple(sorted(edges.items())))
        A.need(t['graph_sha256']==G.sha(fingerprint),'every complete frontier/candidate graph independently re-enumerated')
        if kind=='dead':return False
        if len(points.expand(ids))>len(points.expand(best)):best=list(ids)
        if kind=='empty':leaf=list(ids);return True
        stats['forced' if kind=='forced' else 'branches']+=1;children=t['children']
        A.need(tuple(x['candidate'] for x in children)==tuple(choices[:len(children)]),'complete domain branch-order prefix')
        for j,child in enumerate(children):
            cid=child['candidate'];stats['base_attempts']+=len(points.tiles[cid]['members']);stats['tile_attempts']+=1;ok=visit(child['tree'],ids+[cid])
            if ok is not False:A.need(j==len(children)-1 and 'cutoff' not in t,'stop at successful or open child');return ok
            stats['backtracks']+=1
        if 'cutoff' in t:
            A.need(len(children)<len(choices),'open unexecuted suffix');reason=t['cutoff'];next_cost=len(points.tiles[choices[len(children)]]['members'])
            A.need(reason in ('wall_before_candidate','attempts_before_candidate'),'declared cutoff')
            A.need(r['seconds']>=r['limits']['seconds'] if reason.startswith('wall') else stats['base_attempts']+next_cost>r['limits']['base_attempts'],'actual budget condition');cuts+=1;return None
        A.need(len(children)==len(choices),'finite exhaustion covers every candidate');return False
    root=r['search_tree'] if r['search_tree'] is not None else r['partial_tree'];ok=visit(root,[])
    expected='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope';A.need(expected==r['status'] and cuts==int(ok is None),'tri-state outcome and single open suffix')
    A.need((r['search_tree'] is None)==(ok is None) and (r['partial_tree'] is None)==(ok is not None),'complete/open tree distinction')
    A.need(all(r[k]==v for k,v in stats.items()) and stats['base_attempts']<=r['limits']['base_attempts'],'all expanded work');chosen=leaf if ok else best;A.need(r['selected']==tuple(chosen) and r['placements']==points.expand(chosen),'actual selected expansion')
    A.need(r['tile_generations']==(1,)*len(chosen),'generation-zero coarse roots');A.need(r['peak_frontier_points']==peaks[0] and r['peak_candidate_nodes']==peaks[1] and r['peak_incidences']==peaks[2],'complete incidence peak accounting')
    A.domains(points.base,n,c['target_id'],r['placements'])
    if ok:
        A.need(r['solution_transactions']==tuple(points.tiles[cid]['item'] for cid in chosen if points.tiles[cid]['item'] is not None),'only actually placed metatiles compact');A.check_decoded(c,n,r)
    else:A.need('decoded' not in r and 'solution_transactions' not in r,'no proof on unknown or finite failure')
    return dict(**stats,cutoffs=cuts,exact_solution=ok is True,coarse_points=len(points.root),metatile_types=len(points.items))

def csp_run(c,n,r):
    universe=A.candidates(c,n);keys=[sorted(k for k in universe if k[0]==i) for i in range(n)];maps=[[universe[k] for k in row] for row in keys];full=[(1<<len(row))-1 for row in keys];index=[]
    for row in maps:
        present={};values={}
        for k,m in enumerate(row):
            for p,v in m.items():present[p]=present.get(p,0)|(1<<k);values[p,v]=values.get((p,v),0)|(1<<k)
        index.append((present,values))
    def support(i,k,j):
        mask=full[j];present,values=index[j]
        for p,v in maps[i][k].items():mask&=(full[j]^present.get(p,0))|values.get((p,v),0)
        return mask
    initial=[]
    for i in range(n):
        mask=0
        for k,m in enumerate(maps[i]):
            if n-1 not in m or m[n-1]==c['target_id']:mask|=1<<k
        initial.append(mask)
    stats=dict(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,support_tests=0,removed_values=0,revisions=0);leaf=None;cuts=0
    def visit(t,incoming):
        nonlocal leaf,cuts
        stats['nodes']+=1;A.need(t['incoming']==tuple(hex(x) for x in incoming),'exact classical incoming domains');ds=list(incoming);queue=collections.deque((i,j) for i in range(n) for j in range(n) if i!=j)
        if not all(ds):A.need(t['kind']=='dead' and not t['revisions'] and not t['children'] and t['domains']==tuple(hex(x) for x in ds),'initial empty domain');return False
        dead=False
        for i,j,removed_hex in t['revisions']:
            A.need(queue and queue.popleft()==(i,j) and not dead,'complete ordered AC revision prefix');removed=0
            for k in bits(ds[i]):
                stats['support_tests']+=1
                if not support(i,k,j)&ds[j]:removed|=1<<k
            A.need(hex(removed)==removed_hex,'every removed value has no support; every surviving value does');stats['revisions']+=1;stats['removed_values']+=count(removed);ds[i]&=~removed
            if not ds[i]:dead=True
            elif removed:queue.extend((k,i) for k in range(n) if k!=i and k!=j)
        A.need(t['domains']==tuple(hex(x) for x in ds),'exact propagated domains')
        if dead:A.need(t['kind']=='dead' and not t['children'] and 'cutoff' not in t,'proved dead classical node');return False
        if t.get('cutoff')=='wall_ac':A.need(queue and not t['children'] and r['seconds']>=r['limits']['seconds'],'open AC queue at wall');cuts+=1;return None
        A.need(not queue,'arc-consistency fixed point before branching')
        if all(count(x)==1 for x in ds):
            A.need(t['kind']=='empty' and not t['children'],'complete singleton assignment');leaf=tuple(keys[i][next(bits(mask))] for i,mask in enumerate(ds));return True
        i=min((i for i in range(n) if count(ds[i])>1),key=lambda i:(count(ds[i]),i));choices=list(bits(ds[i]));A.need(t['kind']=='branch' and t['slot']==i,'classical MRV rule');stats['branches']+=1;children=t['children'];A.need(tuple(x['value'] for x in children)==tuple(choices[:len(children)]),'all surviving classical alternatives retained')
        for j,x in enumerate(children):
            stats['base_attempts']+=1;child=list(ds);child[i]=1<<x['value'];ok=visit(x['tree'],child)
            if ok is not False:A.need(j==len(children)-1 and 'cutoff' not in t,'classical stops on first success/open child');return ok
            stats['backtracks']+=1
        if 'cutoff' in t:
            reason=t['cutoff'];A.need(len(children)<len(choices) and reason in ('wall_before_candidate','attempts_before_candidate'),'classical open suffix');A.need(r['seconds']>=r['limits']['seconds'] if reason.startswith('wall') else stats['base_attempts']>=r['limits']['base_attempts'],'classical actual budget');cuts+=1;return None
        A.need(len(children)==len(choices),'classical finite exhaustion');return False
    ok=visit(r['search_tree'] if r['search_tree'] is not None else r['partial_tree'],initial);expected='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope'
    A.need(r['status']==expected and cuts==int(ok is None) and all(r[k]==v for k,v in stats.items()) and stats['base_attempts']<=r['limits']['base_attempts'],'classical exact work and outcome');A.need((r['search_tree'] is None)==(ok is None) and (r['partial_tree'] is None)==(ok is not None),'classical complete/open distinction');A.need(r['base_universe']==r['candidate_universe']==len(universe),'same full original finite candidate universe');A.need(r['placements']==(leaf if ok else ()) and r['solution_transactions']==(),'classical primitive solution')
    if ok:A.domains(universe,n,c['target_id'],leaf);A.check_decoded(c,n,r)
    else:A.need('decoded' not in r,'classical unknown is not a proof')
    return dict(**stats,cutoffs=cuts,exact_solution=ok is True)

def audit(path=DOCS/'coarse-proofs-001.json'):
    start=time.perf_counter();path=Path(path);raw=json.loads(path.read_text());d=freeze(raw);code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program']
    for name,pin in raw['sources'].items():A.need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==pin,'frozen measured source '+name)
    A.need(d['configuration']==dict(seconds=5,base_attempts=50000,index_instances=1000000,replicas=2,native_steps=100000000,lanes=LANES),'exact comparison declaration');A.need(not d['initial_library'] and d['program_sha256']==G.sha(code),'empty library and kernel binding')
    library,donors=B.discoveries(d,code);external_donors,external=G.external();probe=d['whole_library_native'];A.need(probe['request']['blocks']==tuple(t['definition'] for t in library) and probe['request']['theory']==freeze(external_donors['donor-1']['theory']),'whole fresh library');native_binding(code,json.loads(A.packed(probe['request'])),json.loads(A.packed(probe['result'])));A.need(probe['result']['status']=='accepted','complete library native gate')
    A.need([x['problem']['id'] for x in d['evaluation']]==list(external),'all held-out statements');reports=[]
    for i,row in enumerate(d['evaluation']):
        p=row['problem'];A.need(all(p[k]==freeze(v) for k,v in external[p['id']].items()),'independent external statement');c=row['catalog'];A.need(c['theory']==p['theory'] and c['target']==p['target'] and c['configuration']['term_bound']==p['term_bound'] and G.sha(c)==row['catalog_sha256'],'exact original grammar');inventory=A.equation_inventory(c);runs=[]
        for replica in range(2):
            shift=(i+replica)%len(LANES);expected=LANES[shift:]+LANES[:shift];actual=[r for r in row['runs'] if r['replica']==replica];A.need(tuple(r['lane'] for r in actual)==expected,'rotating timing order')
            for run in actual:
                lane=run['lane'];selected=library if lane in ('fine-meta','coarse2-meta','coarse3-meta') else ();r=run['result'];A.need(run['catalog_sha256']==row['catalog_sha256'] and run['library']==tuple(t['name'] for t in selected),'unchanged original grammar and declared frozen types');A.need(r['limits']==dict(seconds=5,base_attempts=50000),'actual request limits')
                if lane=='csp':report=csp_run(c,p['length'],r)
                else:A.need(r['width']==(3 if lane=='coarse3-meta' else 2 if lane.startswith('coarse2') else 1),'declared contraction');report=point_run(c,p['length'],r,selected)
                if 'decoded' in r:
                    report['hierarchy']=G.hierarchy_audit(c,p['length'],r,run['hierarchy'],selected);native_binding(code,json.loads(A.packed(run['hierarchy']['request'])),json.loads(A.packed(run['native'])));report['native_status']=run['native']['status']
                else:A.need('hierarchy' not in run and 'native' not in run,'no false certificate')
                runs.append(dict(lane=lane,replica=replica,report=report))
        reports.append(dict(id=p['id'],inventory=inventory,runs=runs));print('audited',p['id'],flush=True)
    report=dict(status='passed',seconds=time.perf_counter()-start,donors=donors,evaluation=reports,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Independent full bounded inventory and hierarchy mining, every coarse capacity/ownership transition and global decision, every classical support deletion and MRV prefix, every complete or open tree, all expanded proofs and native program/input bindings. No universal compiler proof or native-instruction replay.')
    raw['independent_audit']=report;path.write_text(json.dumps(raw,separators=(',',':'))+'\n');return report
if __name__=='__main__':
    r=audit();print('passed',round(r['seconds'],3))
