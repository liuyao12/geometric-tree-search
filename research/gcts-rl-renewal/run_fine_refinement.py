"""Fine-only response to the exact fixed coarse-root point boundary.

The initial base constituents are all seeded at generation zero. Their sum
equals the aggregate root. Future base tiles have no cluster channels, so the
frozen root's cluster values cannot exclude them. No completion is imported.
"""
import dataclasses,hashlib,json,resource,time
from hierarchy_bridge import HERE,DOCS,definitions,normal
from cluster_learning import corona,check_corona_positive,check_corona_failure
from turtle import Model

def main():
    start=time.monotonic();path=DOCS/'hierarchy-bridge-001.json';d=json.loads(path.read_text())
    names=('local-parent-5',)+tuple(d['ten_types']);ts={t['identity']:t for t in d['inventories']['free']}
    fingerprint=hashlib.sha256(json.dumps(d['inventories'],separators=(',',':')).encode()).hexdigest();rows=[]
    for name in names:
        t=ts[name];r=corona(Model(),t['expansion'],4000,15);r['root']=name
        if r['status']=='positive':assert check_corona_positive(Model(),t['expansion'],r['witness'])
        elif r['status']=='negative':assert check_corona_failure(Model(),t['expansion'],r['certificate'])[0]
        rows.append(r);print(name,r['status'],r['nodes'],round(r['seconds'],3),flush=True)
    d['fine_only_refinement']={'rows':rows,'seconds':time.monotonic()-start,'inventory_sha256':fingerprint,
        'nodes':4000,'cooperative_seconds':15,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'scope':'same aggregate root positive-support boundary expanded into fixed base seeds; complete base-only future candidates; all exposed obligations checked before success; different candidate inventory from aggregate controls'}
    d['sources']['run_fine_refinement.py']=hashlib.sha256((HERE/'run_fine_refinement.py').read_bytes()).hexdigest()
    path.write_text(json.dumps(d,separators=(',',':'))+'\n')

if __name__=='__main__':main()
