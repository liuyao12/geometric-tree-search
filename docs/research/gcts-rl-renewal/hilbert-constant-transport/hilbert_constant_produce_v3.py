"""Bounded structural-only phase; no native queries or point model imports."""
import copy,gzip,hashlib,json,resource,signal,sys,time
from pathlib import Path
import hilbert_constant_checker_v3 as C
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
class Budget(Exception):pass
def setup():
    reports=[]
    for kind,label in [(resource.RLIMIT_DATA,'RLIMIT_DATA'),(resource.RLIMIT_AS,'RLIMIT_AS/RSS')]:
        old=resource.getrlimit(kind)
        try:
            finite=[512*1024*1024]+[x for x in old if x!=resource.RLIM_INFINITY];target=min(finite)
            resource.setrlimit(kind,(target,old[1]));reports.append(dict(name=label,status='set_soft',prior=list(old),requested_soft=target,actual=list(resource.getrlimit(kind))))
        except (ValueError,OSError) as e:reports.append(dict(name=label,status='unsupported',reason=str(e),prior=list(old)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(Budget('wall ceiling')));signal.alarm(180)
    return reports
def rss():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
def guard():
    if rss()>512*1024*1024:raise Budget('peak RSS ceiling')
def raw(p):
    guard();b=p.read_bytes();guard();return b
def load(p):
    b=raw(p);return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def file_sha(p):return hashlib.sha256(raw(p)).hexdigest()
def write(p,x):
    b=(json.dumps(x,indent=2)+'\n').encode();guard();p.write_bytes(gzip.compress(b,mtime=0) if p.suffix=='.gz' else b);guard()
def source_inputs(plan):
    for rel,p in plan['source_pins'].items():
        C.need(file_sha(ROOT/rel)==p['sha256'] and (ROOT/rel).stat().st_size==p['bytes'],'frozen source '+rel)
    entries=0
    for rel,info in plan['preserved_manifests'].items():
        C.need(file_sha(ROOT/rel)==info['sha256'],'immutable prior manifest');m=load(ROOT/rel)
        for pin in m['files']:
            q=ROOT/pin['path'];C.need(file_sha(q)==pin['sha256'] and q.stat().st_size==pin['bytes'],'preserved file '+pin['path']);entries+=1
    for rel,p in plan['inputs'].items():C.need(file_sha(ROOT/rel)==p['sha256'] and (ROOT/rel).stat().st_size==p['bytes'],'frozen input '+rel)
    source=load(ROOT/plan['source_snapshot']);record=load(ROOT/plan['source_record'])[0];receipt=load(ROOT/plan['source_receipt'])
    C.need(source['blocks']==record['request']['blocks'] and source['source_theory']==record['request']['theory'],'source full declarations')
    C.need(record['request_sha256']==C.sha(record['request'])==source['source_request_sha256']==receipt['request_sha256'],'source canonical request')
    C.need(record['result']['status']==receipt['native_outcome']=='accepted' and receipt['status']=='passed' and record['result']['micro_steps']==receipt['native_micro_steps'],'actual accepted/full replay receipts')
    binding=dict(request_sha256=record['request_sha256'],input_sha256=record['input_sha256'],output_sha256=record['output_sha256'],
        native_record_file_sha256=plan['inputs'][plan['source_record']]['sha256'],native_receipt_file_sha256=plan['inputs'][plan['source_receipt']]['sha256'],
        native_micro_steps=record['result']['micro_steps'])
    return source,binding,entries
def apply_mutation(cert,case):
    value=copy.deepcopy(cert);path=case['path'];at=value
    for key in path[:-1]:at=at[key]
    op=case['operation'];key=path[-1]
    if op=='set':at[key]=copy.deepcopy(case['value'])
    elif op=='delete':del at[key]
    elif op=='append':at[key].append(copy.deepcopy(at[key][case['copy_index']]))
    elif op=='swap':at[key][case['left']],at[key][case['right']]=at[key][case['right']],at[key][case['left']]
    else:raise ValueError('unknown mutation')
    return value
def main():
    os_limits=setup();began=time.perf_counter();plan=load(HERE/'plan-v3.json');phase='binding'
    try:
        C.need(plan['budgets']==dict(production_wall_seconds=180,audit_wall_seconds=180,host_ceiling_bytes=512*1024*1024),'approved gates')
        stage=time.perf_counter();source,binding,entries=source_inputs(plan);bind_seconds=time.perf_counter()-stage
        phase='construction';stage=time.perf_counter();theory,records,aliases=C.reconstruct(source)
        cert=dict(version='hilbert-closed-constant-certificate-1',authority='finite_structural_preservation_only',source_native_binding=binding,recipient_theory=theory,records=records,dependency_aliases=aliases)
        construction=time.perf_counter()-stage;guard();phase='checking';stage=time.perf_counter();checked=C.check(cert,source,binding);checking=time.perf_counter()-stage;guard()
        phase='corruptions';stage=time.perf_counter();reports=[]
        for case in plan['certificate_corruptions']:
            mutant=apply_mutation(cert,case);guard()
            try:C.check(mutant,source,binding)
            except (C.Invalid,KeyError,IndexError,TypeError) as e:reports.append(dict(name=case['name'],status='rejected',mutant_sha256=C.sha(mutant),reason=str(e)))
            else:raise ValueError('corruption accepted '+case['name'])
        for case in plan['primitive_corruptions']:
            index=case['record_index'];d=records[index]['definition'];mutant=apply_mutation(d,case)
            available={r['definition']['name']:r['definition'] for r in records[:index]};guard()
            try:C.check_block(mutant,theory,theory['axioms'],available)
            except (C.Invalid,KeyError,IndexError,TypeError) as e:reports.append(dict(name=case['name'],status='rejected',mutant_sha256=C.sha(mutant),reason=str(e)))
            else:raise ValueError('primitive corruption accepted '+case['name'])
        # Duplicate raw JSON names are rejected before AST checking.
        duplicate=b'{"version":"first","version":"second"}'
        try:C.strict_json(duplicate)
        except C.Invalid:reports.append(dict(name='raw-duplicate-json-field',status='rejected',mutant_sha256=hashlib.sha256(duplicate).hexdigest(),reason='duplicate JSON field'))
        else:raise ValueError('duplicate raw field accepted')
        corruption_seconds=time.perf_counter()-stage
        phase='serialization';stage=time.perf_counter();write(HERE/'certificate-v3.json.gz',cert);write(HERE/'corruptions-v3.json',reports);serialization=time.perf_counter()-stage
        promoted=[r for r in records if r['family']=='searched-incidence-transport'];positive=dict(coincident_common_points=sum(r['constant_map']['A']==r['constant_map']['B'] for r in promoted),coincident_lines=sum(r['constant_map']['u']==r['constant_map']['v'] for r in promoted),transport_equals_A=sum(r['constant_map']['C']==r['constant_map']['A'] for r in promoted),transport_equals_B=sum(r['constant_map']['C']==r['constant_map']['B'] for r in promoted))
        guard();result=dict(**checked,plan_sha256=file_sha(HERE/'plan-v3.json'),certificate_sha256=file_sha(HERE/'certificate-v3.json.gz'),corruptions=len(reports),rejected_corruptions=len(reports),positive_noninjective_counts=positive,
            binding_seconds=bind_seconds,construction_seconds=construction,checking_seconds=checking,corruption_seconds=corruption_seconds,serialization_seconds=serialization,production_seconds_before_final_result_write=time.perf_counter()-began,peak_rss_bytes=rss(),preserved_file_entries=entries,os_limits=os_limits,
            scope='Finite closed-constant instances of the exact six-rule host structural relation; not formal native-program correspondence, fresh native acceptance, proof search or activated authority. Timers include preparation/source binding, all checks and serialization; final result-file write is separately included in harness elapsed.')
        write(HERE/'production-v3.json',result);print(json.dumps(result),flush=True)
    except (Budget,MemoryError) as e:
        write(HERE/'production-v3.json',dict(status='unknown_structural_resource',phase=phase,reason=str(e),seconds=time.perf_counter()-began,peak_rss_bytes=rss(),native_queries=0,point_models=0,target_searches=0));raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
