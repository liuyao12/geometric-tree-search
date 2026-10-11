"""Versioned streaming serialization repair, with unchanged request semantics.

All 94 requests use their independently audited existing heap estimates. This
phase only serializes the same initial geometry in small chunks. It executes
no checker, native admission or proof search. Earlier memory unknowns stay intact.
"""
import copy,gzip,hashlib,json,resource,signal,struct,time
from pathlib import Path
from audit_certificate_boundary import initial_for,pin
from audit_proof_boundary import PINNED_MICRO,PINNED_PROGRAM

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011';OUT=PARENT/'capacity-stream'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def need(t,m):
    if not t:raise ValueError(m)
def alarm(*a):raise TimeoutError('unknown_stream_capacity_time_budget')
def arm(plan,began):
    remaining=plan['ceilings']['batch_seconds']-(time.perf_counter()-began);need(remaining>0,'unknown_stream_capacity_batch_time_budget');signal.setitimer(signal.ITIMER_REAL,min(remaining,plan['ceilings']['per_request_seconds']))
def check(plan,began):
    need(time.perf_counter()-began<=plan['ceilings']['batch_seconds'],'unknown_stream_capacity_batch_time_budget');need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=plan['ceilings']['rss_bytes'],'unknown_stream_capacity_memory_budget')
def request(theory,d):
    t=['imp',['bot'],['bot']];return dict(protocol='gcts-fol-1',theory=theory,blocks=[d],proof=[dict(rule='tautology',formula=t)],target=t)
def layout(initial):
    start=1;out=[]
    for i,(word,head,cap) in enumerate(zip(initial['words'],initial['heads'],initial['capacities'])):
        out.append(dict(band=i,header_origin=start,body_origin=start+1,terminator=start+cap+1,logical_head=head,physical_head=start+1+head,capacity=cap,word_sha256=hashlib.sha256(word.encode()).hexdigest()));start+=cap+2
    return out
def write_stream(initial,alphabet,path):
    """Exactly the frozen GTM3 format, at most 16,384 integers per chunk."""
    ids={s:i for i,s in enumerate(alphabet)};digest=hashlib.sha256();length=0;chunk=16384;blank=struct.pack('<I',ids['B']);blanks=blank*chunk
    with path.open('wb') as target:
        with gzip.GzipFile(fileobj=target,mode='wb',mtime=0,filename='') as out:
            def emit(data):
                nonlocal length
                out.write(data);digest.update(data);length+=len(data)
            emit(struct.pack('<II',0x47544d33,len(initial['words'])))
            for word,head,cap in zip(initial['words'],initial['heads'],initial['capacities']):
                need(0<=head<cap and len(word)+1<=cap,'valid unchanged initial band');emit(struct.pack('<III',cap,head,ids['^']))
                for first in range(0,len(word),chunk):
                    part=word[first:first+chunk];emit(struct.pack('<'+'I'*len(part),*(ids[s] for s in part)))
                count=cap-1-len(word)
                while count>=chunk:emit(blanks);count-=chunk
                if count:emit(blank*count)
    return dict(input_sha256=digest.hexdigest(),input_bytes=length)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());result=dict(status='running_versioned_stream_encoding_only',observations=[],native_queries=0,target_searches=0);signal.signal(signal.SIGALRM,alarm)
    try:
        arm(plan,began)
        for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen streaming binding '+p)
        partial=json.loads((PARENT/'capacity-full/partial-audit/audit.json').read_text());need(partial['status']=='passed_all94heap_and37encoding_partial_replay','complete existing heap estimates');old=json.loads((PARENT/'capacity-full/summary.json').read_text());need(old['status']=='unknown_full_capacity_memory_budget' and len(old['encodings'])==37,'original unknown preserved');metrics={q['definition_name']:q for q in load(PARENT/'capacity-full/partial-audit/all94-metrics.json.gz')};items=load(PARENT/'attempt-02/admission-requirements.json.gz');by={q['name']:q for q in items};need(plan['all_names']==sorted(by)==sorted(metrics) and len(by)==94,'entire inventory order');common=1
        while common<max(q['required_heap_capacity'] for q in metrics.values())+64:common*=2
        need(common==plan['common_heap_capacity']==partial['common_heap_capacity'] and common<=plan['ceilings']['physical_heap_cells'],'unchanged audited geometry');micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and pin(boundary['program'])==PINNED_PROGRAM,'same parser/checker/palette');theory=load(PARENT/'attempt-02/two-lemmas-retained-core.json.gz')['spec']['theory']
        for j,name in enumerate(plan['all_names']):
            arm(plan,began);stage=time.perf_counter();req=request(theory,by[name]['definition']);need(pin(req)==by[name]['request_sha256']==metrics[name]['request_sha256'],'exact whole request');original=initial_for(micro,boundary['cases'][0]['initial'],req);initial=copy.deepcopy(original);initial['capacities'][micro['heap']]=common;file=OUT/('input-%03d.bin.gz'%j);encoded=write_stream(initial,micro['raw'],file);obs=dict(index=j,definition_name=name,request_sha256=pin(req),original_initial=original,proposed_initial=initial,original_layout=layout(original),proposed_layout=layout(initial),native_start_state=micro['start'],physical_origin=0,**encoded,encoded_file_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),encoded_file_bytes=file.stat().st_size,required_heap_capacity=metrics[name]['required_heap_capacity'],physical_width=sum(initial['capacities'])+2*len(initial['capacities'])+2,seconds=time.perf_counter()-stage);save(OUT/('frame-%03d.json.gz'%j),obs);result['observations'].append({k:obs[k] for k in ('index','definition_name','request_sha256','input_sha256','input_bytes','encoded_file_sha256','encoded_file_bytes','required_heap_capacity','physical_width','seconds')});check(plan,began);result.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print('STREAM ENCODING CHECKPOINT',j,encoded['input_bytes'],flush=True);del req,original,initial,obs;__import__('gc').collect()
        result.update(status='complete_all94_stream_encodings_pending_independent_replay',complete_request_encodings=94,common_heap_capacity=common,original_full_memory_unknown_preserved=True,prior_saved_encoding_comparisons_required=45,native_admissions_fresh_unresolved=93,scope='Serialization-only infrastructure repair. Exact whole requests, initial words/heads/state/origin and band capacities unchanged from audited common geometry. No changed theory, parser/checker/palette, native admission or proof search.')
    except (ValueError,MemoryError,TimeoutError) as e:result.update(status=str(e),failure_type=type(e).__name__);raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);result.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
