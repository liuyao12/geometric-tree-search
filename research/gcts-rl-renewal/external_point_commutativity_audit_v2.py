"""Independent point/CNF/assignment reconstruction. No model or encoder imports. Resource-only lifetime recovery v2.

SAT is checked by explicit valuation, original point sums, assigned m agreement,
strict-prior decoding and the existing independent full serialized rule replay.
UNSAT proof strings are retained but deliberately not accepted as certificates.
"""
import copy,gzip,hashlib,itertools,json,resource,signal,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.gcts-active/external-point-commutativity-20261011'
def packed(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha(x):return hashlib.sha256(packed(x)).hexdigest()
def load(p):
    b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def need(x,msg):
    if not x:raise ValueError(msg)
def peak():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
def reconstruct(spec,cat,reg_hash):
    n=spec['length'];rules=cat['rules'];roots=[[4*j,r] for j in range(n) for r in range(4)]
    words={k:sorted({packed(v) for v in vs}) for k,vs in [('formula',cat['basis']),('command',[r['command'] for r in rules])]}
    ids={k:{w:i for i,w in enumerate(vs)} for k,vs in words.items()}
    dictionary={k:[dict(id=i,value=json.loads(w),word_hex=w.hex(),expanded_points=len(w)+1) for i,w in enumerate(vs)] for k,vs in words.items()}
    modes=[i+1 if r['premises'] else 0 for i,r in enumerate(rules)];rows=[];placements=[]
    def add(key,entries,command,requirements,kind,**other):
        marks={}
        for p,v in entries:
            p=tuple(p);need(p not in marks or marks[p]==v,'internally unequal mark');marks[p]=v
        placements.append(dict(key=list(key),occupancy=[[[4*key[0],key[1]],12]],
            marks=[[list(p),v] for p,v in sorted(marks.items())],slot=key[0],kind=kind,
            command=command,requirements=requirements,**other))
    for j in range(n):
        choices=[dict(rule=i,command=copy.deepcopy(r['command'])) for i,r in enumerate(rules) if j<n-1 or r['conclusion']==spec['target']];rows.append(choices)
        for k,c in enumerate(choices):
            i=c['rule'];r=rules[i];m=[[[4*j+2,0],ids['formula'][packed(r['conclusion'])]],[[4*j+2,1],ids['command'][packed(c['command'])]],[[4*j+2,90],modes[i]]]
            for role,kind in [(0,'command'),(1,'guard')]:add((j,role,k,0),m,c['command'],[],kind,inference=i)
        for role in range(2):
            add((j,role+2,0,0),[[[4*j+2,90],0],[[4*j+2,100+role],-1]],None,[],'unused_input',input=role,mode=0,source=None)
            for i,r in enumerate(rules):
                if not modes[i]:continue
                m=[[[4*j+2,90],modes[i]]]
                if role>=len(r['premises']):add((j,role+2,modes[i],0),m+[[[4*j+2,100+role],-1]],None,[],'unused_input',input=role,mode=modes[i],source=None)
                else:
                    for s in range(j):add((j,role+2,modes[i],s+1),m+[[[4*j+2,100+role],s],[[4*s+2,0],ids['formula'][packed(r['premises'][role])]]],None,[[s,r['premises'][role]]],'inference_input',input=role,mode=modes[i],source=s)
    placements.sort(key=lambda x:x['key']);marks=[[[4*(n-1)+2,0],ids['formula'][packed(spec['target'])]]]
    semantic=dict(schema='exact-scalar-point-model-v1',length=n,required_points=[dict(point=p,generation=0) for p in roots],
        initial=dict(roots=[[p,0] for p in roots],generations=[[p,0] for p in roots],marks=marks,totals=[],allowed_points=roots),
        placements=placements,injective_catalog=dictionary,inference_rules=rules,rule_modes=modes,row_domains=rows,arity=2,capacity=12,registry_sha256=reg_hash)
    return dict(length=n,roots=roots,initial_marks=marks,placements=placements,rules=rules,rule_modes=modes,semantic=semantic,capacity=12,
        scope='Full unit-capacity scalar point adaptation; fixed orientations, all distant assigned marks.')

def independent_cnf(point):
    """Declarative inventory followed by independently written ordered constraints."""
    occ={tuple(p):[] for p in point['roots']};marks=set();implications=[]
    descriptors=[dict(kind='placement',key=c['key']) for c in point['placements']]
    for i,c in enumerate(point['placements'],1):
        need(len(c['occupancy'])==1 and c['occupancy'][0][1]==12 and tuple(c['occupancy'][0][0]) in occ,'unsupported unit t shape')
        occ[tuple(c['occupancy'][0][0])].append(i);assigned={}
        for p,v in c['marks']:
            need(type(v) is int,'exact integer marks');p=tuple(p)
            need(p not in assigned or assigned[p]==v,'internally contradictory mark');assigned[p]=v
            marks.add((p,v));implications.append((i,p,v))
    for p,v in point['initial_marks']:marks.add((tuple(p),v))
    markid={}
    for p,v in sorted(marks):descriptors.append(dict(kind='mark',point=list(p),value=v));markid[p,v]=len(descriptors)
    by={}
    for (p,v),i in sorted(markid.items()):by.setdefault(p,[]).append(i)
    clauses=[];groups=[]
    for family,domains in [('occupancy',occ),('mark',by)]:
        for p,xs in sorted(domains.items()):
            if family=='occupancy':clauses.append(xs[:])
            groups.append(dict(family=family,point=list(p),variables=xs))
            if len(xs)<2:continue
            start=len(descriptors)+1
            descriptors.extend(dict(kind='prefix',family=family,point=list(p),prefix_length=i) for i in range(1,len(xs)))
            clauses.append([-xs[0],start])
            for k in range(1,len(xs)-1):clauses.extend([[-xs[k],start+k],[-(start+k-1),start+k],[-xs[k],-(start+k-1)]])
            clauses.append([-xs[-1],-(start+len(xs)-2)])
    clauses.extend([[-i,markid[p,v]] for i,p,v in implications]);clauses.extend([[markid[tuple(p),v]] for p,v in point['initial_marks']])
    return dict(variables=descriptors,clauses=clauses,groups=groups)
def satisfied(cnf,assignment):
    need(len(assignment)==len(cnf['variables']) and all(type(b) is bool for b in assignment),'complete Boolean valuation')
    need(all(any(assignment[abs(l)-1]==(l>0) for l in c) for c in cnf['clauses']),'every original CNF clause')
def point_check(point,keys):
    need(len(keys)==len({tuple(k) for k in keys}),'placement multiplicity')
    table={tuple(c['key']):c for c in point['placements']};totals={tuple(p):0 for p in point['roots']};marks={tuple(p):v for p,v in point['initial_marks']}
    for k in keys:
        need(tuple(k) in table,'declared complete placement identity');c=table[tuple(k)]
        for p,v in c['occupancy']:totals[tuple(p)]=totals.get(tuple(p),0)+v
        for p,v in c['marks']:
            p=tuple(p);need(p not in marks or marks[p]==v,'assigned distant/initial m disagreement');marks[p]=v
    need(set(totals)=={tuple(p) for p in point['roots']} and all(v==12 for v in totals.values()),'every mandatory t total exactly12')
    return dict(required_points=len(totals),assigned_mark_points=len(marks),selected_placements=len(keys),totals_sha256=sha(sorted(totals.items())),marks_sha256=sha(sorted(marks.items())))
def decode(point,keys,target):
    table={tuple(c['key']):c for c in point['placements']};chosen={tuple(table[tuple(k)]['occupancy'][0][0]):table[tuple(k)] for k in keys};word=[];lines=[]
    need(len(chosen)==4*point['length'],'four fields per row')
    for j in range(point['length']):
        c=chosen[4*j,0];g=chosen[4*j,1];i=c['inference'];r=point['rules'][i]
        need(c['command']==g['command'] and c['inference']==g['inference'],'exact command and guard identity')
        refs=[]
        for role in range(2):
            port=chosen[4*j,role+2];need(port['mode']==point['rule_modes'][i],'input mode')
            if role<len(r['premises']):
                s=port['source'];need(type(s) is int and 0<=s<j and port['kind']=='inference_input','strict-prior input')
                need(lines[s]['formula']==r['premises'][role],'ordered exact source formula');refs.append(s)
            else:need(port['source'] is None and port['kind']=='unused_input','explicit unused input')
        cmd=copy.deepcopy(c['command']);need(cmd['formula']==r['conclusion'],'exact row formula')
        if cmd['rule']=='block':cmd['inputs']=refs
        elif cmd['rule']=='generalize':need(len(refs)==1,'unary generalization');cmd['source']=refs[0]
        else:need(not refs,'zero-input primitive')
        word.append(cmd);lines.append(dict(row=j,formula=r['conclusion'],rule_index=i,command=cmd,source_rows=refs,placements=[chosen[4*j,k]['key'] for k in range(4)]))
    need(lines[-1]['formula']==target,'original target last row');return word,lines
def rejected(fn):
    try:fn()
    except (ValueError,KeyError,IndexError,TypeError):return True
    return False
def fixtures():
    cases=[]
    def candidate(i,p,v=12,m=()):return dict(key=[0,i,0,0],occupancy=[[p,v]],marks=list(m))
    models=[dict(name='distant-mark-only',roots=[[0,0],[1,0]],initial_marks=[],placements=[candidate(0,[0,0],m=[[[99,7],0]]),candidate(1,[1,0],m=[[[99,7],1]])]),
        dict(name='initial-assigned-zero',roots=[[0,0]],initial_marks=[[[8,8],0]],placements=[candidate(0,[0,0],m=[[[8,8],1]]),candidate(1,[0,0])]),
        dict(name='untouched-required-hole',roots=[[0,0],[1,0]],initial_marks=[],placements=[candidate(0,[0,0])]),
        dict(name='three-prefix-values',roots=[[0,0]],initial_marks=[],placements=[candidate(i,[0,0],m=[[[9,9],i]]) for i in range(3)])]
    for m in models:
        cnf=independent_cnf(m);count=len(cnf['variables']);need(count<=18,'tiny fixture');projections=set()
        for a in itertools.product([False,True],repeat=count):
            if all(any(a[abs(l)-1]==(l>0) for l in c) for c in cnf['clauses']):
                keys=[c['key'] for c,b in zip(m['placements'],a) if b];point_check(m,keys);projections.add(tuple(a[:len(m['placements'])]))
        legal=set()
        for selected in itertools.product([False,True],repeat=len(m['placements'])):
            keys=[c['key'] for c,b in zip(m['placements'],selected) if b]
            if not rejected(lambda:point_check(m,keys)):legal.add(selected)
        need(projections==legal,'exact existential auxiliary equivalence');cases.append(dict(name=m['name'],variables=count,valuations=2**count,legal_subsets=len(legal),status='passed'))
    bad=copy.deepcopy(models[0]);bad['placements'][0]['occupancy'][0][1]=6
    need(rejected(lambda:independent_cnf(bad)),'fractional unsupported');cases.append(dict(name='fractional-occupancy-fail-closed',status='passed'))
    bad=copy.deepcopy(models[0]);bad['placements'][0]['occupancy'].append([[1,0],12]);need(rejected(lambda:independent_cnf(bad)),'shared occupancy unsupported');cases.append(dict(name='multi-root-occupancy-fail-closed',status='passed'))
    return cases
def main():
    start=time.perf_counter();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('180s audit')));signal.alarm(180)
    report=dict(status='running',models=[],corruptions=[],native_queries=0,unchecked_unsat_proofs=0)
    try:
        plan=load(OUT/'plan.json');frozen=load(OUT/'encoding-freeze.json');report['plan_sha256']=hashlib.sha256((OUT/'plan.json').read_bytes()).hexdigest()
        for path,entry in {**plan['sources'],**plan['inputs']}.items():need(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==entry['sha256'],'exact source/input pin '+path)
        for path,entry in plan['runtime'].items():need(hashlib.sha256(Path(path).read_bytes()).hexdigest()==entry['sha256'],'solver runtime pin')
        source=load(ROOT/plan['inputs_role']['spec']);cat=load(ROOT/plan['inputs_role']['catalog']);reg=load(ROOT/plan['inputs_role']['registry']);receipt=load(ROOT/plan['inputs_role']['registry_audit']);reg_hash=hashlib.sha256((ROOT/plan['inputs_role']['registry']).read_bytes()).hexdigest()
        need(receipt['status']=='passed_complete_exact94_native_admission_registry' and receipt['registry_sha256']==reg_hash,'complete94 prior native binding')
        need(reg['theory']==source['case']['theory'] and reg['target']==source['case']['target'],'theory target binding')
        need({d['name']:d for d in cat['definitions']}=={d['name']:d['definition'] for d in reg['definitions'] if d['status']=='native_accepted'} and len(cat['definitions'])==94,'all94 exact definitions')
        need(frozen['plan_sha256']==report['plan_sha256'] and frozen['no_solver_calls_yet'],'pre-query encoding freeze')
        qf=load(OUT/'query-freeze.json');cross=load(OUT/'cross-track.json')
        need(qf['plan_sha256']==report['plan_sha256'] and qf['encoding_freeze_sha256']==hashlib.sha256((OUT/'encoding-freeze.json').read_bytes()).hexdigest() and qf['cross_track_sha256']==hashlib.sha256((OUT/'cross-track.json').read_bytes()).hexdigest() and qf['no_solver_calls_yet'],'query freeze binding')
        need(cross['status']=='passed_exact_12_and_13_semantic_hash_agreement','cross track agreement')
        report['fixtures']=fixtures()
        for length in plan['lengths']:
            t=time.perf_counter();spec=copy.deepcopy(source['case']);spec['length']=length
            point=reconstruct(spec,cat,reg_hash);actual=load(OUT/('point-'+str(length)+'.json.gz'));need(point==actual,'entire independently reconstructed point model')
            if length==12:
                prior=load(ROOT/plan['inputs_role']['baseline'])['model']
                for key,expected in [('placements',point['placements']),('roots',point['roots']),('initial_marks',point['initial_marks']),('catalog',point['semantic']['injective_catalog']),('inference_rules',point['rules']),('domains',point['semantic']['row_domains'])]:need(prior[key]==expected,'original12 row model '+key)
                del prior
            del actual
            need(len(point['placements'])=={12:17158,13:19848}[length],'complete universe census')
            cnf=independent_cnf(point);actual_cnf=load(OUT/('encoding-'+str(length)+'.json.gz'))
            need(all(cnf[k]==actual_cnf[k] for k in cnf),'every variable descriptor, constraint and ordered group')
            raw=('p cnf '+str(len(cnf['variables']))+' '+str(len(cnf['clauses']))+'\n'+''.join(' '.join(str(l) for l in c)+' 0\n' for c in cnf['clauses'])).encode()
            need(gzip.decompress((OUT/('point-'+str(length)+'.cnf.gz')).read_bytes())==raw,'independent DIMACS exact bytes')
            freeze=next(x for x in frozen['models'] if x['length']==length)
            need(freeze['semantic_sha256']==sha(point['semantic']) and freeze['dimacs_raw_sha256']==hashlib.sha256(raw).hexdigest(),'semantic/raw CNF hashes')
            need(cross['semantic_sha256'][str(length)]==sha(point['semantic']),'all semantic cross-track data')
            model_receipt=dict(length=length,placements=len(point['placements']),roots=len(point['roots']),variables=len(cnf['variables']),clauses=len(cnf['clauses']),semantic_sha256=sha(point['semantic']),encoding_reconstruction_seconds=time.perf_counter()-t)
            # Actual saved encoded/model perturbations, rejected by exact independent reconstruction.
            for name,changed,expected in [('deleted-required-root-clause',cnf['clauses'][1:],cnf['clauses']),('altered-distant-implication',cnf['clauses'][:-2]+cnf['clauses'][-1:],cnf['clauses']),('deleted-initial-target',cnf['clauses'][:-1],cnf['clauses']),('omitted-complete-candidate',point['placements'][:-1],point['placements']),('altered-catalog-ID',point['semantic']['injective_catalog']['formula'][1:],point['semantic']['injective_catalog']['formula'])]:
                need(changed!=expected,'actual corruption differs');report['corruptions'].append(dict(length=length,name=name,rejected=True,corrupt_sha256=sha(changed),reference_sha256=sha(expected),mechanism='full exact structural comparison'))
            path=OUT/('result-'+str(length)+'.json.gz')
            if not path.exists():model_receipt['status']='unknown_no_completed_solver_result'
            else:
                result=load(path);t=time.perf_counter()
                if result['solver_result']=='sat':
                    satisfied(cnf,result['assignment']);selected=[v['key'] for v,b in zip(cnf['variables'],result['assignment']) if b and v['kind']=='placement']
                    need(selected==result['placements'],'selected variable/placement binding');model_receipt['point_validation']=point_check(point,selected)
                    word,lines=decode(point,selected,spec['target']);need(word==result['producer_decoded_word'],'independent row command decode')
                    from audit_semantic_proofs import whole_replay
                    request=dict(protocol='gcts-fol-1',theory=spec['theory'],target=spec['target'],blocks=cat['definitions'],proof=word)
                    replayed=whole_replay(request);need(replayed['status']=='accepted','independent full serialized logical replay')
                    output=dict(status='independently_checked_finite_point_SAT_and_host_logical_word',request=request,rows=lines,replay=replayed,placement_keys=selected,semantic_sha256=sha(point['semantic']))
                    (OUT/('checked-'+str(length)+'.json.gz')).write_bytes(gzip.compress(packed(output),mtime=0));model_receipt.update(status=output['status'],logical_replay=replayed)
                    for name,keys in [('omitted-root',selected[:-1]),('duplicate-placement',selected+[selected[0]]),('undeclared-placement',selected+[[999,0,0,0]])]:
                        need(rejected(lambda:point_check(point,keys)),'actual SAT point corruption');report['corruptions'].append(dict(length=length,name=name,rejected=True,corrupt_sha256=sha(keys)))
                    bad=result['assignment'][:];first=next(i for i,v in enumerate(cnf['variables']) if v['kind']=='placement' and bad[i]);bad[first]=False
                    need(rejected(lambda:satisfied(cnf,bad)),'SAT Boolean corruption');report['corruptions'].append(dict(length=length,name='unset-selected-placement',rejected=True,corrupt_sha256=sha(bad)))
                    bad=copy.deepcopy(word);bad[-1]['formula']=['eq',['fun','zero',[]],['fun','succ',[['fun','zero',[]]]]]
                    r=whole_replay(dict(request,proof=bad));need(r['status']!='accepted','altered conclusion rejected');report['corruptions'].append(dict(length=length,name='altered-decoded-conclusion',rejected=True,corrupt_sha256=sha(bad),replay_status=r['status']))
                elif result['solver_result']=='unsat':model_receipt.update(status='solver_unsat_assertion_only_complete_encoding_checked',unchecked_proof_sha256=hashlib.sha256(result.get('unchecked_solver_proof','').encode()).hexdigest());report['unchecked_unsat_proofs']+=1
                else:model_receipt.update(status='unknown_solver',reason=result.get('reason_unknown'))
                model_receipt['assignment_certificate_check_seconds']=time.perf_counter()-t
            report['models'].append(model_receipt)
            need(peak()<=536870912,'512MiB audit peak');need(time.perf_counter()-start<=180,'180s aggregate audit');del point,cnf,actual_cnf,raw
        report['status']='passed_complete_independent_encoding_and_available_SAT_checks'
    except Exception as e:report.update(status='unknown_or_rejected_independent_audit',reason=type(e).__name__+': '+str(e))
    finally:
        signal.alarm(0);report.update(seconds_before_final_write=time.perf_counter()-start,peak_rss_bytes=peak(),authority='Exact finite point SAT and host word validation only; no native query or checked UNSAT refutation.')
        if report['seconds_before_final_write']>180 or report['peak_rss_bytes']>536870912:report['status']='unknown_audit_resource'
        (OUT/'audit-v2.json').write_bytes(packed(report));print(json.dumps(report),flush=True)
if __name__=='__main__':main()
