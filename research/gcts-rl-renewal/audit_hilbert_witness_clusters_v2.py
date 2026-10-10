"""Corrected independent grammar, provenance, family and trace replay.

Version 001 expected a theory field in statement metadata that intentionally
contains only the symbolic target/context. The measured producer and source
pins remain unchanged. This version binds the complete catalog theory to the
reviewed foundation and records its own audit source separately.


No generator, search, graph, point-model, miner or producer imports. Reviewed
statement hashes and the published foundation fix the external experiment.
"""
import gzip,hashlib,json,time
from pathlib import Path
import audit_hilbert_quantified as Q
import audit_induction_proofs as I
import audit_induction_clusters as H
from audit_semantic_proofs import need,packed
from audit_serialized_kernel import freeze,replay
from audit_proof_compaction import native_binding

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
PINS={'line-has-point':'bf1ea7a2e74182028a6c16a261fbeab6a6985bfba506e54967d6312223e42895','unique-joining-line':'0de0c24dc35889e6b52b6d282f21f768be2b43138683ac3ce0616856e0a81953','joining-exists-reordered':'602c6986925291255c3fb69759a87ec679bbf5d55e698b14f2bf89dade98bdae'}
LANES=('gcts-base','gcts-motifs','csp-base','csp-motifs')
MATRIX=(('unique-joining-line','unique-joining-line',12,(),2),('joining-exists-reordered','joining-exists-reordered',7,(),2),('joining-no-I1','unique-joining-line',12,('I.1-existence',),1),('joining-no-I2','unique-joining-line',12,('I.2-uniqueness',),1),('joining-short','unique-joining-line',11,(),1))
SOURCES=H.MEASURED_SOURCES+('euclidean_proof_tiles.py','hilbert_incidence_tiles.py','quantified_proof_rules.py','hilbert_quantified_tiles.py','audit_hilbert_incidence.py','audit_hilbert_quantified.py','test_hilbert_quantified.py','run_hilbert_quantified.py','indexed_proof_clusters.py','hilbert_witness_clusters.py','test_indexed_proof_clusters.py','run_hilbert_witness_clusters.py','audit_hilbert_witness_clusters.py')
def sha(blob):return hashlib.sha256(blob).hexdigest()
def load(descriptor,folder):
    need(descriptor['file']==folder+'/'+descriptor['id']+'.json.gz','fixed shard name')
    blob=(DOCS/descriptor['file']).read_bytes();raw=gzip.decompress(blob)
    need(sha(blob)==descriptor['sha256'] and len(blob)==descriptor['bytes'] and sha(raw)==descriptor['raw_sha256'] and len(raw)==descriptor['raw_bytes'],'whole shard byte binding')
    row=json.loads(raw);need(row['id']==descriptor['id'] and row['problem']==descriptor['problem'],'descriptor binding')
    return freeze(row)
def audit():
    path=DOCS/'hilbert-witness-clusters-001.json';raw=json.loads(path.read_text());d=freeze(raw);began=time.perf_counter()
    need(set(d['sources'])==set(SOURCES),'entire measured source set')
    for name,pin in d['sources'].items():need(sha((HERE/name).read_bytes())==pin,'frozen measured source '+name)
    need(H.sha((d['foundation'],d['foundation_metadata']))=='92bb283fb033ab6048565d1f09ffc19ac441fe0a82f108e82e30f30b443a6f01','published Hilbert foundation')
    need(sha(packed(d['native_program']))=='5f3aaf81e325654d30cc116a8f412c3152e75ccb4e0d781882180e8d0ec1fa31','unchanged native proof checker')
    need(d['initial_library']==() and d['policy'] is None,'no prior library/policy')
    need(d['configuration']==dict(seconds=30,donor_seconds=30,base_attempts=10000,native_steps=1000000000,lanes=LANES,motif_sizes=(2,3),marked=True),'fixed limits and lanes')
    cache={}
    def bound(row):
        p=row['problem'];c=row['catalog'];name=p['id']
        need(H.sha(p)==PINS[name],'externally fixed statement/bounds')
        need(c['target']==p['target'] and c['configuration']['hypothesis']==p['hypothesis'] and c['configuration']['goal']==p['goal'] and c['configuration']['context_transport']==p['transport'],'target/context binding')
        need(H.sha(c)==row['catalog_sha256'],'entire grammar pin')
        omit=c['configuration']['omit'];expected=dict(d['foundation'],axioms={n:a for n,a in d['foundation']['axioms'].items() if n not in omit})
        need(packed(c['theory'])==packed(expected),'exact source foundation minus omissions')
        if row['catalog_sha256'] not in cache:cache[row['catalog_sha256']]=Q.inventory(c)
        return c,p
    def positive(c,r,run):
        request=r['decoded']['request'];proof=replay(packed(request))
        need(proof['status']=='accepted' and packed(proof['proof'])==packed(run['primitive_proof']) and proof['expanded_lines']==run['primitive_lines'],'complete primitive proof')
        native_binding(d['native_program'],request,run['native']);need(run['native']['status']=='accepted','complete native acceptance')
        return proof['expanded_lines']
    need(tuple(x['id'] for x in d['donors'])==('line-has-point',),'single fresh donor')
    donor=load(raw['donors'][0],'hilbert-cluster-donors-001');c,p=bound(donor);run=donor['run'];r=run['result']
    need(r['marking']=='support' and r['limits']==dict(seconds=30,base_attempts=10000),'donor resource and budget')
    report=I.point_run(c,p['length'],r);need(report['exact_solution'],'source discovered')
    report['primitive_lines']=positive(c,r,run)
    # The frozen merger retains the first occurrence object and appends later
    # provenance to its sources list. Reconstruct that storage alias explicitly:
    # all occurrence rows remain, and the first duplicate row has the union.
    # Nothing is accepted from producer metadata without reconstructing every
    # connected source fragment and the exact merged library independently.
    occurrences=H.learned(c,r,p);merged=H.merged([occurrences])
    need(freeze(occurrences)==donor['mined'],'all connected fragments including merger provenance aliases')
    need(freeze(merged)==d['library'],'complete independently reconstructed library')
    library=dict(patterns=len(merged),source_occurrences=sum(len(t['sources']) for t in merged),storage='First duplicate source row shares the merged provenance list; reconstructed exactly.')
    need(d['library_sha256']==H.sha(d['library']),'entire learned library')
    print('audited fresh donor',p['id'],flush=True)
    need(tuple(x['id'] for x in d['cases'])==tuple(x[0] for x in MATRIX),'all nominated recipients/controls')
    cases=[]
    for i,(descriptor,expected) in enumerate(zip(raw['cases'],MATRIX)):
        name,base,n,omit,replicas=expected;row=load(descriptor,'hilbert-cluster-cases-001');c,p=bound(row)
        need(row['id']==name and p['id']==base and row['length']==n and row['omit']==omit and c['configuration']['omit']==omit and row['replicas']==replicas,'declared control')
        order=[]
        for replica in range(replicas):
            shift=(i+replica)%4;order.extend((replica,lane) for lane in LANES[shift:]+LANES[:shift])
        need(tuple((x['replica'],x['lane']) for x in row['runs'])==tuple(order),'rotating complete trial matrix')
        runs=[]
        for run in row['runs']:
            r=run['result'];active=d['library'] if run['lane'].endswith('motifs') else ()
            need(run['catalog_sha256']==row['catalog_sha256'] and r['marked'] is True and r['limits']==dict(seconds=30,base_attempts=10000),'same grammar/resources/budget')
            trace=(H.csp_run if run['lane'].startswith('csp') else H.point_run)(c,n,r,active)
            if trace['exact_solution']:trace['primitive_lines']=positive(c,r,run)
            else:need('native' not in run and 'primitive_proof' not in run,'no certificate at cutoff/exhaustion')
            runs.append(dict(lane=run['lane'],replica=run['replica'],report=trace))
            print('audited',name,run['replica'],run['lane'],flush=True)
        cases.append(dict(id=name,runs=runs))
    raw['independent_audit']=dict(status='passed',auditor=dict(file=Path(__file__).name,sha256=sha(Path(__file__).read_bytes()),prior_attempt=dict(status='failed',file='audit_hilbert_witness_clusters.py',reason='Statement metadata has no theory field; corrected complete theory binding uses the catalog and reviewed foundation. No search or measured source changed.')),seconds=time.perf_counter()-began,donor=report,library=library,inventories=list(cache.values()),cases=cases,scope='Independent complete syntax/block reconstruction including quantifier scope; every connected donor fragment and certificate provenance; all formula/contact family instances; exact aggregate occupancy/markings; every global decision, AC deletion, prefix, rollback, base fallback, budget, primitive and native binding. Atomic motifs preserve exact solutions, not primitive scheduling traces. No recursive receptor composition or RL audit is claimed.')
    path.write_text(json.dumps(raw,separators=(',',':'))+'\n');print('audit passed',round(raw['independent_audit']['seconds'],4),flush=True)
    return raw['independent_audit']
if __name__=='__main__':audit()
