"""Acquire a pinned two-polymorph corpus; keep simulation metadata out of geometry.

Matching input-deck state points do not assign those conditions to TRAIN.traj.
No checkpoint or downloaded Python code is executed.
"""
import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import numpy as np
from ase.io import read

repo='water-ice-group/MolCrys-MACE';commit='36a5da6583bdce806d4e5ece5c4c0e355076a887'
out=Path(sys.argv[1]);out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
configs=[];records=[];files=[];protocols=[]
for phase,folder in [('alpha','14_oxalic_acid_alpha'),('beta','15_oxalic_acid_beta')]:
    root=f'CMD_QMD_INPUT_OUTPUT_FILES/{folder}/solid/classic'
    paths=[f'FINE_TUNED_MACE_MODELS/{folder}/TRAIN.traj']+[f'{root}/{name}' for name in ['input.xml','init.xyz','simulation.out','run-ase.py']]
    local={}
    for relative in paths:
        dest=out/f'{phase}-{Path(relative).name}';url=f'https://raw.githubusercontent.com/{repo}/{commit}/{relative}'
        subprocess.run(['curl','-fsSL','--max-time','60',url,'-o',str(dest)],check=True)
        files.append(dict(path=relative,url=url,localFile=dest.name,sha256=sha(dest),bytes=dest.stat().st_size));local[Path(relative).name]=dest
    xml=ET.parse(local['input.xml']).getroot();ensemble=xml.find('.//ensemble')
    temp=ensemble.find('temperature');pressure=ensemble.find('pressure')
    assert temp.attrib['units']=='kelvin' and pressure.attrib['units']=='bar'
    protocols.append(dict(phase=phase,temperatureK=float(temp.text),pressurePa=100000*float(pressure.text),
                          dynamics=xml.find('.//dynamics').attrib['mode'],beads=int(xml.find('.//initialize').attrib['nbeads']),
                          seed=int(xml.find('.//prng/seed').text),inputHash=sha(local['input.xml']),
                          conditionScope='This input deck only; not mapped to training frames',
                          requestedTrajectory=xml.find('.//output/trajectory').attrib))
    frames=read(local['TRAIN.traj'],index=':');phase_rows=[]
    for i,a in enumerate(frames):
        assert np.isfinite(a.positions).all() and np.isfinite(a.cell.array).all()
        periodic=bool(all(a.pbc) and np.linalg.det(a.cell.array)>0)
        cid=f'oxalic-{phase}-{i:04d}'
        record=dict(id=cid,phase=phase,sourceFrame=i,sourceHash=sha(local['TRAIN.traj']),atoms=len(a),
                    elements=sorted(set(a.get_chemical_symbols())),composition=dict(Counter(a.get_chemical_symbols())),
                    periodic=periodic,infoKeys=sorted(a.info),arrayKeys=sorted(a.arrays),
                    calculatorKeys=sorted(a.calc.results) if a.calc is not None else [],
                    temperatureK=None,pressurePa=None,trajectoryId=None,
                    conditionAdmission='unmapped training configurations; do not inherit MD input conditions')
        phase_rows.append(record);records.append(record)
        if periodic:
            configs.append(dict(id=cid,species=a.get_chemical_symbols(),positions=a.positions.tolist(),cell=a.cell.array.tolist(),pbc=a.pbc.tolist()))
    print(json.dumps(dict(phase=phase,frames=len(frames),periodic=sum(r['periodic'] for r in phase_rows),atomCounts=dict(Counter(r['atoms'] for r in phase_rows)),infoKeys=sorted({k for r in phase_rows for k in r['infoKeys']}))),flush=True)
target=out/'coordinates.json'
with target.open('x') as f:json.dump(dict(configurations=configs),f)
report=dict(scope=__doc__,repository=repo,commit=commit,codeHash=sha(Path(__file__)),files=files,protocols=protocols,
            configurations=records,coordinateHash=sha(target),
            matchedDeckStatePoints=len({(p['temperatureK'],p['pressurePa'],p['dynamics'],p['beads']) for p in protocols})==1,
            admittedConditionMatchedFrames=0,
            limits='Geometry-only development corpus. Phase and source metadata are excluded from learner coordinates. The two MD decks share state points but are not a mapping of TRAIN.traj to those runs. Output trajectories and independent-run identifiers have not been acquired. No learned motifs, reconstruction or growth result yet.')
with (out/'provenance.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(periodicConfigurations=len(configs),matchedDeckStatePoints=report['matchedDeckStatePoints'],admittedConditionMatchedFrames=0)))
