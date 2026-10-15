import time
BEGAN_NS=time.perf_counter_ns()
import hashlib,json,subprocess,sys
from pathlib import Path
RUNTIME='/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'
EXPECTED='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
raw=Path(RUNTIME).read_bytes()
if hashlib.sha256(raw).hexdigest()!=EXPECTED or len(raw)!=102352:raise ValueError('pinned runtime mismatch')
child_source="import time,json,sys; print(json.dumps({'perf_ns':time.perf_counter_ns(),'monotonic_ns':time.monotonic_ns(),'version':sys.version,'implementation':time.get_clock_info('perf_counter').implementation}),flush=True)"
rows=[]
for index in range(2):
 time.sleep(.2)
 before=time.perf_counter_ns()
 remaining=20-(before-BEGAN_NS)/1e9
 if remaining<=0:raise TimeoutError('runtime calibration joint20')
 proc=subprocess.Popen([RUNTIME,'-I','-B','-c',child_source],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:out,err=proc.communicate(timeout=remaining)
 except BaseException:
  proc.kill();proc.communicate();raise
 after=time.perf_counter_ns()
 if proc.returncode!=0 or err or not out.endswith(b'\n') or out.count(b'\n')!=1:raise ValueError('whole native child outcome')
 value=json.loads(out)
 rows.append({'index':index,'parent_before_ns':before,'parent_after_ns':after,'child':value,'perf_bracketed':before<=value['perf_ns']<=after,'reaped':True,'exit_code':proc.returncode})
finished=time.perf_counter_ns()
if finished-BEGAN_NS>=20000000000:raise TimeoutError('calibration completed outside20')
result={'schema':'ROOT-NONLOGICAL-runtime-clock-ABI-probe-v1','scope':'two fresh pinned runtime processes only; no project Source/functions/Q/model/fixtures/proof search','runtime_sha256':EXPECTED,'parent_version':sys.version,'parent_clock_implementation':time.get_clock_info('perf_counter').implementation,'began_ns':BEGAN_NS,'finished_ns':finished,'elapsed_ns':finished-BEGAN_NS,'rows':rows,'shared_perf_origin_bracket_control_passed':all(x['perf_bracketed'] for x in rows),'proof_accepted':False,'full_architecture_qualified':False,'resource_fit_accepted':False,'project_functions_executed':0}
print(json.dumps(result,sort_keys=True),flush=True)
