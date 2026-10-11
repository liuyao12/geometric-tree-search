"""Independent Cartesian pilot selection, fixed-program replay and encoding.

No producer import. All94requests participate in deterministic size-strata
selection; a separate stack interpreter computes every instruction/heap event.
Every proposed initial word/capacity/head and encoded byte is reconstructed.
"""
import collections,gzip,hashlib,json,resource,signal,struct,time
from pathlib import Path
import audit_tree_kernel as T
from audit_certificate_boundary import initial_for,pin
from audit_proof_boundary import expected_constructor,PINNED_MICRO,PINNED_PROGRAM,code_bytes

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011';OUT=PARENT/'capacity-pilot'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def alarm(*a):raise TimeoutError('unknown_commutativity_capacity_audit_time_budget')
def encode(initial,alphabet):
    vals=[0x47544d33,len(initial['words'])]
    for word,head,cap in zip(initial['words'],initial['heads'],initial['capacities']):vals.extend([cap,head,alphabet.index('^')]+[alphabet.index(x) for x in word]+[alphabet.index('B')]*(cap-1-len(word)))
    return struct.pack('<'+'I'*len(vals),*vals)
def bases(caps):
    pos=1;starts=[]
    for cap in caps:starts.append(pos+1);pos+=cap+2
    return starts,pos+1
def main():
    began=time.perf_counter();ap=json.loads((OUT/'audit-plan.json').read_text());plan=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text());result=dict(status='auditing',observations=[],native_queries=0,target_searches=0);signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,ap['ceilings']['seconds'])
    try:
        for p,h in {**plan['source_sha256'],**ap['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen exact pilot input/source '+p)
        need(summary['status']=='complete_capacity_pilot_pending_independent_replay','complete estimates required');core=load(PARENT/'attempt-02/two-lemmas-retained-core.json.gz');reqs=load(PARENT/'attempt-02/admission-requirements.json.gz');description={r['command']['name']:r['description'] for r in core['rules'] if r['command']['rule']=='block'};strata=collections.defaultdict(list);theory=core['spec']['theory'];taut=['imp',['bot'],['bot']]
        for row in reqs:
            desc=description[row['name']];key=(desc['operation'],desc.get('move',{}).get('rule',{}).get('origin','none'));req=dict(protocol='gcts-fol-1',theory=theory,blocks=[row['definition']],proof=[dict(rule='tautology',formula=taut)],target=taut);word=json.dumps(req,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode();need(hashlib.sha256(word).hexdigest()==row['request_sha256'] and len(word)==row['request_json_bytes'],'all94 exact inventory requests');strata[key].append((len(word),row['name'],req,row))
        selected=[]
        for key,entries in sorted(strata.items()):
            size,name,req,row=max(entries,key=lambda a:(a[0],a[1]));selected.append(dict(stratum=list(key),definition_name=name,request=req,request_sha256=row['request_sha256'],request_json_bytes=size,stratum_complete_request_count=len(entries)))
        need(selected==plan['selected_requests'] and len(selected)==8,'entire inventory generic maximum selection, no outcome chosen');micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and pin(boundary['program'])==PINNED_PROGRAM,'fixed parser/checker/palette');T.static_program(boundary['program']);observations=load(OUT/'estimates.json.gz');need(len(observations)==len(selected),'all declared exact pilot requests accounted')
        for j,(selected,obs) in enumerate(zip(selected,observations)):
            start=time.perf_counter();need(obs['request']==selected['request'] and obs['request_sha256']==selected['request_sha256'] and obs['query']==j,'exact selected full request');initial=initial_for(micro,boundary['cases'][0]['initial'],selected['request']);nodes,root=expected_constructor(micro,initial,selected['request']);need(initial==obs['original_initial'] and nodes==obs['constructor_nodes'] and root==obs['constructor_root'],'actual parser construction binding');need(hashlib.sha256(encode(initial,micro['raw'])).hexdigest()==obs['original_input_sha256'],'entire original initial encoding');work=[];validate=T.validate_heap
            def retain(ns):validate(ns);work.append(ns)
            T.validate_heap=retain
            try:replay=T.replay(boundary['program'],dict(nodes=nodes,node=root),plan['ceilings']['tree_steps'],plan['ceilings']['tree_heap_nodes'],keep=0)
            finally:T.validate_heap=validate
            need(len(work)==1 and [list(n) for n in work[0]]==obs['final_tree_nodes'] and replay=={k:v for k,v in obs['tree_result'].items() if k!='seconds'} and replay['status']=='accepted','every exact independent instruction/event/profile/final-heap result');required=2+sum((i+257).bit_length()+max(1,a.bit_length())+max(1,b.bit_length())+3 for i,(a,b) in enumerate(work[0]));need(required==obs['required_heap_capacity'] and obs['requirement_is_complete'],'all canonical heap record widths independently counted');extended=obs['proposed_initial'];need(extended['words']==initial['words'] and extended['heads']==initial['heads'] and extended['capacities']==[summary['declared_common_heap_capacity'] if t==micro['heap'] else n for t,n in enumerate(initial['capacities'])],'only external blank heap-band capacity changes');raw=encode(extended,micro['raw']);need(raw==gzip.decompress((OUT/('query-%03d-proposed-input.bin.gz'%j)).read_bytes()) and hashlib.sha256(raw).hexdigest()==obs['proposed_input_sha256'] and len(raw)==obs['proposed_input_bytes'],'entire independent proposed native encoding');b0,w0=bases(initial['capacities']);b1,w1=bases(extended['capacities']);delta=extended['capacities'][micro['heap']]-initial['capacities'][micro['heap']];need(all(b1[t]-b0[t]==(0 if t<=micro['heap'] else delta) for t in range(len(b0))),'every later physical band displaced correctly');result['observations'].append(dict(query=j,stratum=obs['stratum'],request_sha256=obs['request_sha256'],tree_steps=replay['steps'],heap_nodes=len(work[0]),required_heap_capacity=required,proposed_heap_capacity=extended['capacities'][micro['heap']],original_heap_capacity=initial['capacities'][micro['heap']],physical_width_before=w0,physical_width_after=w1,proposed_input_sha256=obs['proposed_input_sha256'],all_payload_symbols_and_local_heads_unchanged=True,seconds=time.perf_counter()-start));(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('COMMUTATIVITY INDEPENDENT CAPACITY CHECKPOINT',j,required,flush=True);need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=ap['ceilings']['rss_bytes'],'unknown_commutativity_capacity_audit_memory_budget');del work,raw;__import__('gc').collect()
        desired=1
        while desired<max(o['required_heap_capacity'] for o in observations)+plan['safety_blank_cells']:desired*=2
        need(desired==summary['declared_common_heap_capacity'] and summary['micro_code_bytes_sha256']==hashlib.sha256(code_bytes(micro)).hexdigest(),'generic common capacity and exact universal code bytes');result.update(status='passed_complete_selected_capacity_and_encoding_replay',declared_common_heap_capacity=desired,selected_queries=8,complete_inventory_requests=94,unselected_capacity_estimates_unresolved=86,program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,scope='Eight size-stratified exact-request fixed-program/heap and encoding estimates only. Every selected initial byte and unchanged parser/checker/palette pin is independently matched. No native execution, target proof, cluster-search/GCTS/RL result or all94capacity guarantee.')
    except (ValueError,MemoryError,TimeoutError) as e:result.update(status=str(e),failure_type=type(e).__name__);raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);result.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
