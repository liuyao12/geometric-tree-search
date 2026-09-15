"""Prespecified ordering follow-up on all six frozen phase-expansion frames."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--node',required=True)
p.add_argument('--policy',choices=['interleaved','coupled-observed'],default='interleaved')
a=p.parse_args();here=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a.output.mkdir()
ordering_module='coupled-endpoint-search.mjs' if a.policy=='coupled-observed' else 'interleaved-factorized-search.mjs'
manifest={'policy':a.policy,'phases':['Ih','II','VI'],'budgetSecondsPerFrame':30,
          'parentManifestHash':digest(a.source/'manifest.json'),'configurations':read(a.source/'manifest.json')['configurations'],
          'orderingHash':digest(here/ordering_module),
          'scope':'Same registered model and markings; only candidate enumeration order changes. No oracle witness or training cover is supplied to the search policy. Developmental follow-up, not blind validation.'}
if a.policy=='coupled-observed':
    manifest['scope']='Restricted learned hypothesis retaining only paired endpoint source observations. Not equivalent to factorized model. Same finite registrations, half t values and reference scheduler; no training-cover or oracle-answer replay. Developmental comparison, not blind validation.'
with (a.output/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
rows=[]
for phase in manifest['phases']:
    source=a.source/phase;out=a.output/phase
    subprocess.run([a.node,str(here/'ice-dynamic-factorized-search.mjs'),str(source/'source.json'),str(source/'filtered.json'),
                    str(out),str(source/'index.json'),str(source/'index-check.json'),a.policy],check=True)
    check_path=a.output/f'{phase}-check.json'
    subprocess.run([sys.executable,str(here/'verify-ice-factorized-search.py'),str(source/'source.json'),str(source/'filtered.json'),str(out),str(check_path)],check=True)
    summary=read(out/'summary.json');check=read(check_path)
    assert summary['sourceModelHash']==check['sourceModelHash']==digest(source/'source.json')
    assert summary['blocksHash']==check['blocksHash']==digest(source/'filtered.json')
    assert summary['sourceHashes']['coupledModel' if a.policy=='coupled-observed' else 'interleavedOrdering']==manifest['orderingHash']
    for result,verified in zip(summary['results'],check['results'],strict=True):
        assert result['file']==verified['file'] and result['selected']==verified['selected']
        assert verified['runHash']==digest(out/f"{result['fold']}.json")
        assert result['rootRollback'] and result['scalarComplete']==verified['complete']
        if verified['complete']:assert result['markingStatus']=='verified-common-values' and verified['verifiedAssignments']==2*verified['selected']
        meta=next(c for c in manifest['configurations'] if c['id']==result['file'])
        rows.append({'phase':phase,'split':'training' if meta['split']=='train' else 'developmental','result':result,'independentCheck':verified,'sourceHashes':summary['sourceHashes'],'checkHash':digest(check_path)})
assert len(rows)==6
with (a.output/'report.json').open('x') as f:json.dump({'manifest':manifest,'results':rows,'completeRuns':sum(r['independentCheck']['complete'] for r in rows)},f,indent=2)
print(json.dumps({'checkedFrames':len(rows),'complete':sum(r['independentCheck']['complete'] for r in rows)}),flush=True)
