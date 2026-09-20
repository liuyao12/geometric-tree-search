"""Training-only whole-motif port co-occurrences from frozen interfaces.

Interface model IDs identify frozen geometric point/value pairs, not new
marking channels. This is a strict co-occurrence control, not a proof that
other geometric combinations are forbidden.
"""
import hashlib,json,sys
from pathlib import Path
from collections import Counter,defaultdict

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    metap,motifp,interfacep,out=map(Path,sys.argv[1:5]);mode=sys.argv[5] if len(sys.argv)>5 else 'recurring-only';assert mode in ['recurring-only','all-training-ports']
    meta=json.loads(metap.read_text());motifs=json.loads(motifp.read_text());interfaces=json.loads(interfacep.read_text())
    assert interfaces['metadataHash']==sha(metap) and interfaces['motifHash']==sha(motifp)
    mm={r['id']:r for r in meta['configurations']};rr={r['id']:r for r in motifs['rows']};contexts=[];lookup={};usage=defaultdict(set);rows=[];repeat_ports=[]
    for frame in sorted(interfaces['frames'],key=lambda r:(not r['training'],r['configuration'])):
        if frame['status']!='admitted':continue
        cid=frame['configuration'];clusters=rr[cid]['clusters'];ports=[[] for _ in clusters]
        for oi in frame['observations']:
            o=interfaces['observations'][oi];mi=o['interface']
            if mi is None or (mode=='recurring-only' and interfaces['models'][mi]['trainingFrames']<2):continue
            ports[o['clusterA']].append((mi,'A'));ports[o['clusterB']].append((mi,'B'))
        selected=[]
        for k,(cluster,pp) in enumerate(zip(clusters,ports)):
            pp.sort();key=(cluster['type'],tuple(pp));typ=lookup.get(key)
            if len(pp)!=len(set(pp)):repeat_ports.append(dict(configuration=cid,cluster=k,duplicates=[p for p,n in Counter(pp).items() if n>1]))
            if typ is None and frame['training']:
                typ=len(contexts);lookup[key]=typ;contexts.append(dict(baseType=cluster['type'],ports=pp,sourceConfiguration=cid,sourceCluster=k))
            if frame['training']:usage[typ].add(cid)
            selected.append(dict(cluster=k,baseType=cluster['type'],ports=pp,context=typ))
        rows.append(dict(configuration=cid,training=frame['training'],motifs=selected,periodicMatchedGraph=frame['matchedGraph']['connectedPeriodicLift']))
    for k,c in enumerate(contexts):c['trainingFrames']=len(usage[k])
    summary=[]
    for phase in sorted({r['phase'] for r in mm.values()}):
        group=[r for r in rows if not r['training'] and mm[r['configuration']]['phase']==phase]
        summary.append(dict(phase=phase,frames=len(group),motifs=sum(len(r['motifs']) for r in group),exactContexts=sum(p['context'] is not None for r in group for p in r['motifs']),allExactFrames=sum(all(p['context'] is not None for p in r['motifs']) for r in group),allExactConnectedFrames=sum(r['periodicMatchedGraph'] and all(p['context'] is not None for p in r['motifs']) for r in group)))
    report=dict(scope=__doc__,mode=mode,metadataHash=sha(metap),motifHash=sha(motifp),interfaceHash=sha(interfacep),codeHash=sha(Path(__file__)),contexts=contexts,rows=rows,duplicatePorts=repeat_ports,summary=summary,
                limits='Exact port-label co-occurrence audit under the saved first interface assignment. Mode declares whether training ports are filtered to recurring interfaces or all retained. Evaluation rows contain only previously accepted recurring-model matches, not complete target decorations. Different model IDs can carry compatible geometric values; alternative assignments and subsets are not evaluated. Missing co-occurrence is not proof of forbidden geometry. Not GCTS filling/search.')
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(dict(contexts=len(contexts),recurringContexts=sum(c['trainingFrames']>=2 for c in contexts),emptyContexts=sum(not c['ports'] for c in contexts),duplicatePortOccurrences=len(repeat_ports),summary=summary)))
if __name__=='__main__':main()
