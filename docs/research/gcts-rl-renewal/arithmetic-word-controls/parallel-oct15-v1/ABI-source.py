"""ROOT stdlib-only ABI diagnostic. No project code or mathematical data."""
import time
BEGIN=time.clock_gettime_ns(time.CLOCK_MONOTONIC)
import hashlib,json,os,resource,subprocess,sys,tempfile
PYTHON='/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'
assert os.path.realpath(sys.executable)==PYTHON and sys.platform=='darwin'
assert len(sys.argv)==2
plan_raw=open(sys.argv[1],'rb').read();plan=json.loads(plan_raw)
assert plan=={'schema':'ROOT-native-rusage-ABI-probe-v1','scope':'stdlib_only_no_Q_no_project_Source','leaf_allocation_bytes':67108864,'local_limit_seconds':20,'authorized_invocations':1}
leaf_code="""import json,resource
before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
payload=bytearray(67108864)
for i in range(0,len(payload),4096):payload[i]=73
after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({'before_self_bytes':before,'after_self_bytes':after,'touched_bytes':len(payload)},sort_keys=True,separators=(',',':')),flush=True)
"""
parent_before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
child=None;reaped=False
try:
 with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
  child=subprocess.Popen([PYTHON,'-I','-S','-B','-c',leaf_code],stdin=subprocess.DEVNULL,stdout=out,stderr=err,close_fds=True,start_new_session=True,env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})
  while True:
   pid,status,usage=os.wait4(child.pid,os.WNOHANG)
   if pid:
    assert pid==child.pid;child.returncode=os.waitstatus_to_exitcode(status);reaped=True;break
   if time.clock_gettime_ns(time.CLOCK_MONOTONIC)-BEGIN>=20000000000:raise TimeoutError('ABI probe20 only')
   time.sleep(.005)
  out.seek(0);stdout=out.read(4097);err.seek(0);stderr=err.read(4097)
  assert child.returncode==0 and len(stdout)<4096 and stdout.endswith(b'\n') and stderr==b''
  leaf=json.loads(stdout);parent_after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
  record={'schema':'ROOT-native-rusage-parent-observation-v1','plan_sha256':hashlib.sha256(plan_raw).hexdigest(),'begin_ns':BEGIN,'pid':os.getpid(),'child_pid':child.pid,'wait4_pid':pid,'wait4_status':status,'parent_SELF_before_bytes':parent_before,'parent_SELF_after_bytes':parent_after,'parent_CHILDREN_after_bytes':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'leaf_self_record':leaf,'leaf_terminal_wait4_maxrss_bytes':usage.ru_maxrss,'known_children_reaped':True,'observed_before_output_ns':time.clock_gettime_ns(time.CLOCK_MONOTONIC),'Q_payload_parses':0,'project_Source_imports':0,'proof_searches':0,'current_pipeline_admitted':False}
  assert record['observed_before_output_ns']-BEGIN<20000000000
  print(json.dumps(record,sort_keys=True,separators=(',',':')),flush=True)
finally:
 if child is not None and not reaped:
  try:os.killpg(child.pid,9)
  except ProcessLookupError:pass
  pid,status,usage=os.wait4(child.pid,0);child.returncode=os.waitstatus_to_exitcode(status)
