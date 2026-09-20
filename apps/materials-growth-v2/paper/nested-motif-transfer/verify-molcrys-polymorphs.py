"""Independent ASE source replay and strict non-inheritance of input-deck labels."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import numpy as np
from ase.io import read
root,out=map(Path,sys.argv[1:]);p=json.loads((root/'provenance.json').read_text());c=json.loads((root/'coordinates.json').read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert p['coordinateHash']==sha(root/'coordinates.json')
for f in p['files']:assert sha(root/f['localFile'])==f['sha256']
by_id={r['id']:r for r in c['configurations']};assert len(by_id)==len(c['configurations'])
rows=[];decks=[]
for phase in ['alpha','beta']:
    frames=read(root/f'{phase}-TRAIN.traj',index=':');metadata=[r for r in p['configurations'] if r['phase']==phase]
    assert len(frames)==len(metadata)
    volumes=[]
    for frame,(a,r) in enumerate(zip(frames,metadata,strict=True)):
        assert r['sourceFrame']==frame and r['sourceHash']==sha(root/f'{phase}-TRAIN.traj')
        assert r['temperatureK'] is r['pressurePa'] is r['trajectoryId'] is None
        if r['periodic']:
            x=by_id[r['id']];assert set(x)=={'id','species','positions','cell','pbc'}
            assert x['species']==a.get_chemical_symbols() and x['pbc']==a.pbc.tolist()
            assert np.array_equal(x['positions'],a.positions) and np.array_equal(x['cell'],a.cell.array)
            volumes.append(float(a.get_volume()/len(a)))
    xml=ET.parse(root/f'{phase}-input.xml').getroot();e=xml.find('.//ensemble')
    t=e.find('temperature');pressure=e.find('pressure')
    assert t.attrib['units']=='kelvin' and pressure.attrib['units']=='bar'
    deck=(float(t.text),float(pressure.text)*100000,xml.find('.//dynamics').attrib['mode'])
    saved=next(r for r in p['protocols'] if r['phase']==phase)
    assert deck==(saved['temperatureK'],saved['pressurePa'],saved['dynamics']);decks.append(deck)
    rows.append(dict(phase=phase,sourceFrames=len(frames),atomCountDistribution=dict(Counter(len(a) for a in frames)),
                     volumePerAtomRangeAngstrom3=[min(volumes),max(volumes)],allCoordinateRecordsExact=True,
                     frameConditionsAvailable=False,inputDeckStatePoint=dict(temperatureK=deck[0],pressurePa=deck[1],ensemble=deck[2])))
assert len(set(decks))==1 and p['matchedDeckStatePoints'] and p['admittedConditionMatchedFrames']==0
report=dict(provenanceHash=sha(root/'provenance.json'),coordinateHash=sha(root/'coordinates.json'),verifierHash=sha(Path(__file__)),
            rows=rows,conditionMatchedFramesAdmitted=0,
            limits='Exact raw-coordinate and input-deck replay, not proof that frames were generated at the deck conditions. Periodic flags do not identify a thermodynamic phase; the training files contain multiple atom counts. No learned motif or growth result.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
