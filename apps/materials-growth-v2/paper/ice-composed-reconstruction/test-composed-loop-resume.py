"""Synthetic resume/hash/accounting controls; no material result claims."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
node,kernel=sys.argv[1:];runner=Path(__file__).with_name('ice-composed-core-loop.mjs')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='gcts-resume-test-') as tmp:
    p=Path(tmp);modelp=p/'model.json';priorp=p/'prior.json';checkp=p/'check.json'
    model={'models':[{'id':'tiny','model':{'capacity':1,'required':['p'],'complete':True,'radius':.6,'fields':[],'candidates':[{'id':'a','base':'a','t':[{'point':'p','value':1}],'m':[],'fieldM':[]}]}}]}
    modelp.write_text(json.dumps(model));prior={'sourceHash':sha(modelp),'kernelHash':sha(kernel),'cores':[],'rounds':[{},{}],'secondsIncludingRestarts':12.5};priorp.write_text(json.dumps(prior))
    check={'resultHash':sha(priorp),'modelHash':sha(modelp),'verifiedCores':0};checkp.write_text(json.dumps(check))
    output=p/'valid.json';r=subprocess.run([node,str(runner),str(modelp),kernel,str(output),str(priorp),str(checkp)],capture_output=True,text=True);assert r.returncode==0,r.stderr
    result=json.loads(output.read_text());assert result['status']=='complete-awaiting-independent-replay' and result['totalRounds']==3 and result['initialCoreCount']==0
    assert abs(result['cumulativeSeconds']-(12.5+result['secondsIncludingRestarts']))<1e-9
    for name,key in [('wrong_result','resultHash'),('wrong_model','modelHash')]:
        bad=dict(check);bad[key]='0'*64;checkp.write_text(json.dumps(bad));r=subprocess.run([node,str(runner),str(modelp),kernel,str(p/f'{name}.json'),str(priorp),str(checkp)],capture_output=True,text=True)
        assert r.returncode!=0 and 'AssertionError' in r.stderr
    print('Valid resume and cumulative accounting pass; mismatched proof/result and model are rejected.')
