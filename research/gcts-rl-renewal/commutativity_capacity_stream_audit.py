"""Independent all-94 typed-array encoding and exact older-input comparison.

Producer writes chunks directly to gzip; auditor constructs independent native
32-bit arrays. Every initial symbol, head, capacity, physical layout and exact
byte is compared, including all eight pilot and 37 full-run saved encodings.
"""
import array,gzip,hashlib,itertools,json,resource,signal,sys,time
from pathlib import Path
from audit_certificate_boundary import initial_for,pin
from audit_proof_boundary import PINNED_MICRO,PINNED_PROGRAM

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011';OUT=PARENT/'capacity-stream'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def alarm(*a):raise TimeoutError('unknown_stream_audit_time_budget')
def arm(plan,began):
    remaining=plan['ceilings']['batch_seconds']-(time.perf_counter()-began);need(remaining>0,'unknown_stream_audit_batch_time_budget');signal.setitimer(signal.ITIMER_REAL,min(remaining,plan['ceilings']['per_request_seconds']))
def request(theory,d):
    t=['imp',['bot'],['bot']];return dict(protocol='gcts-fol-1',theory=theory,blocks=[d],proof=[dict(rule='tautology',formula=t)],target=t)
def encode(initial,alphabet):
    values=array.array('I');need(values.itemsize==4,'32bit portable format');codes={s:i for i,s in enumerate(alphabet)};values.append(0x47544d33);values.append(len(initial['words']))
    for i in range(len(initial['words'])):
        cap=initial['capacities'][i];word=initial['words'][i];values.append(cap);values.append(initial['heads'][i]);values.append(codes['^']);values.extend(map(codes.__getitem__,word));values.extend(itertools.repeat(codes['B'],cap-len(word)-1))
    if sys.byteorder!='little':values.byteswap()
    return values.tobytes()
def layout(initial):
    out=[]
    for i,cap in enumerate(initial['capacities']):
        origin=1+sum(initial['capacities'][:i])+2*i;word=initial['words'][i];head=initial['heads'][i];out.append(dict(band=i,header_origin=origin,body_origin=origin+1,terminator=origin+cap+1,logical_head=head,physical_head=origin+1+head,capacity=cap,word_sha256=hashlib.sha256(word.encode()).hexdigest()))
    return out
def main():
    began=time.perf_counter();plan=json.loads((OUT/'audit-plan.json').read_text());producer=json.loads((OUT/'summary.json').read_text());result=dict(status='checking_all94_stream_encodings',observations=[],prior_pilot_byte_matches=0,prior_full_byte_matches=0,native_queries=0,target_searches=0);signal.signal(signal.SIGALRM,alarm)
    try:
        arm(plan,began)
        for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen independent stream audit '+p)
        need(producer['status']=='complete_all94_stream_encodings_pending_independent_replay' and len(producer['observations'])==94,'complete producer gate');partial=json.loads((PARENT/'capacity-full/partial-audit/audit.json').read_text());need(partial['status']=='passed_all94heap_and37encoding_partial_replay','all existing heap replay');prior=load(PARENT/'capacity-pilot/estimates.json.gz');pilot_by={q['definition_name']:q for q in prior};pilot_plan=json.loads((PARENT/'capacity-pilot/plan.json').read_text());need(set(pilot_by)=={q['definition_name'] for q in pilot_plan['selected_requests']} and len(pilot_by)==8,'exact frozen eight');old=json.loads((PARENT/'capacity-full/summary.json').read_text());need(old['status']=='unknown_full_capacity_memory_budget' and len(old['encodings'])==37,'memory unknown preserved');metrics={q['definition_name']:q for q in load(PARENT/'capacity-full/partial-audit/all94-metrics.json.gz')};requirements=load(PARENT/'attempt-02/admission-requirements.json.gz');by={q['name']:q for q in requirements};need(sorted(by)==sorted(metrics)==plan['all_names'],'all94 complete inventory');micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and pin(boundary['program'])==PINNED_PROGRAM,'unchanged checker/parser/palette');theory=load(PARENT/'attempt-02/two-lemmas-retained-core.json.gz')['spec']['theory'];common=1
        while common<max(q['required_heap_capacity'] for q in metrics.values())+64:common*=2
        need(common==partial['common_heap_capacity']==plan['common_heap_capacity'],'same external boundary')
        for j,name in enumerate(plan['all_names']):
            arm(plan,began);stage=time.perf_counter();item=by[name];req=request(theory,item['definition']);need(pin(req)==item['request_sha256']==metrics[name]['request_sha256'],'unchanged theory/request');frame=load(OUT/('frame-%03d.json.gz'%j));original=initial_for(micro,boundary['cases'][0]['initial'],req);initial={k:(list(v) if isinstance(v,list) else v) for k,v in original.items()};initial['capacities'][micro['heap']]=common;need(frame['index']==j and frame['definition_name']==name and frame['request_sha256']==pin(req) and frame['original_initial']==original and frame['proposed_initial']==initial,'every initial word/head/capacity');before=layout(original);after=layout(initial);need(frame['original_layout']==before and frame['proposed_layout']==after and frame['physical_origin']==0 and frame['native_start_state']==micro['start']==88986,'every true start/state/origin and physical layout');change=common-original['capacities'][micro['heap']]
            for i,(b,a) in enumerate(zip(before,after)):
                need(a['header_origin']-b['header_origin']==(change if i>micro['heap'] else 0) and a['logical_head']==b['logical_head'] and a['word_sha256']==b['word_sha256'] and a['capacity']-b['capacity']==(change if i==micro['heap'] else 0),'only external heap boundary displacement')
            raw=encode(initial,micro['raw']);file=OUT/('input-%03d.bin.gz'%j);need(raw==gzip.decompress(file.read_bytes()) and hashlib.sha256(raw).hexdigest()==frame['input_sha256']==producer['observations'][j]['input_sha256'] and len(raw)==frame['input_bytes'] and hashlib.sha256(file.read_bytes()).hexdigest()==frame['encoded_file_sha256'],'every independently reconstructed byte');need(frame['physical_width']==sum(initial['capacities'])+2*len(initial['capacities'])+2 and frame['required_heap_capacity']==metrics[name]['required_heap_capacity'],'all frame requirements')
            if name in pilot_by:
                p=pilot_by[name];need(p['request']==req and p['original_initial']==original and p['proposed_initial']==initial and p['proposed_input_sha256']==frame['input_sha256'] and raw==gzip.decompress((PARENT/'capacity-pilot'/('query-%03d-proposed-input.bin.gz'%p['query'])).read_bytes()),'exact earlier eight-pilot byte correspondence');result['prior_pilot_byte_matches']+=1
            if j<37:
                claim=old['encodings'][j];need(claim['index']==j and claim['definition_name']==name and claim['request_sha256']==pin(req) and claim['input_sha256']==frame['input_sha256'] and raw==gzip.decompress((PARENT/'capacity-full'/('input-%03d.bin.gz'%j)).read_bytes()),'exact earlier37full byte correspondence');result['prior_full_byte_matches']+=1
            result['observations'].append(dict(index=j,definition_name=name,request_sha256=pin(req),input_sha256=frame['input_sha256'],input_bytes=len(raw),physical_width=frame['physical_width'],all_initial_and_layout_bytes_matched=True,prior_pilot=name in pilot_by,prior_full=j<37,seconds=time.perf_counter()-stage));need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=plan['ceilings']['rss_bytes'],'unknown_stream_audit_memory_budget');result.update(seconds=time.perf_counter()-began);(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('STREAM INDEPENDENT BYTE CHECKPOINT',j,flush=True);del req,frame,original,initial,raw;__import__('gc').collect()
        need(len(result['observations'])==94 and result['prior_pilot_byte_matches']==8 and result['prior_full_byte_matches']==37,'complete all94+45 prior gate');result.update(status='passed_complete_all94_stream_encoding_and_prior_byte_correspondence',complete_heap_estimates=94,complete_encodings=94,encoding_unresolved=0,common_heap_capacity=common,original_full_memory_unknown_preserved=True,native_admissions_fresh_unresolved=93,program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,scope='Only serialization infrastructure changed. Independent all94 typed-array reconstruction matches streamed bytes, all8pilot/37full prior bytes, exact initial state/origin/words/heads/capacities and every physical boundary. All94 prior independent complete heap estimates retained. No native query or target search; only the separately frozen eight-stratum native pilot may advance.')
    except (ValueError,MemoryError,TimeoutError) as e:result.update(status=str(e),failure_type=type(e).__name__);raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);result.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
