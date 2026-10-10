"""Cold, balanced native palette experiments with full raw search traces."""
import gzip,hashlib,json,statistics,subprocess,time
from pathlib import Path
from native_wang_cases import registry
from shared_wang_inventory import Inventory,TABLE_PIN
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-native-wang-20261010');LANES=['base','neighbors','projected']
SOURCES=('native_wang_domains.cpp','native_wang_search.py','native_wang_cases.py','native_wang_worker.py','run_native_wang_search.py','check_native_rectangle.py','shared_wang_inventory.py','serialized_kernel.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);pins={n:sha(HERE/n) for n in SOURCES};raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());i=Inventory(raw);(TMP/'table.bin').write_bytes(raw)
    before=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'native_wang_domains.cpp'),'-o',str(TMP/'domains')],check=True);compile_seconds=time.perf_counter()-before
    folder=DOC/'native-wang-search-001';folder.mkdir(exist_ok=True);cases=[]
    for index,spec in enumerate(registry(i,DOC)):
        input_path=TMP/'case.json';input_path.write_bytes(canonical(spec));runs=[]
        for rep in range(3):
            off=(index+rep)%3;order=LANES[off:]+LANES[:off]
            for lane in order:
                name='case-'+str(index)+'-'+lane+'-'+str(rep)+'.json.gz';out=folder/name;stage=time.perf_counter()
                subprocess.run(['python3',str(HERE/'native_wang_worker.py'),str(input_path),str(out),str(TMP/'domains'),str(TMP/'table.bin'),lane],check=True)
                r=json.loads(gzip.decompress(out.read_bytes()));runs.append(dict(lane=lane,repetition=rep,order=order,file=str(out.relative_to(DOC)),sha256=sha(out),bytes=out.stat().st_size,stage_seconds=time.perf_counter()-stage,total_seconds=r['result']['total_seconds'],status=r['result']['status'],attempts=r['result']['attempts'],semantic_sha256=r['semantic_sha256']))
        timings={lane:dict(median_seconds=statistics.median(v['total_seconds'] for v in runs if v['lane']==lane),samples=[v for v in runs if v['lane']==lane]) for lane in LANES};cases.append(dict(spec=spec,runs=runs,timings=timings));(TMP/'progress.json').write_bytes(canonical(cases));print('completed',spec['id'],flush=True)
    assert all(sha(HERE/n)==p for n,p in pins.items())
    data=dict(version='native-wang-search-001',sources=pins,literal_table_sha256=TABLE_PIN,inventory_fingerprint=i.fingerprint,tile_types=sum(i.counts.values()),A=i.A,Q=i.Q,D=i.D,lanes=LANES,repetitions=3,cases=cases,compile_seconds=compile_seconds,seconds=time.perf_counter()-began,
        reused_inputs={n:sha(DOC/n) for n in ('proof-boundary-machine-001.bin.gz','proof-boundary-001.json','shared-wang-reader-001.json')},
        scope='Direct complete literal tile domains and reference point scheduling over the unchanged finite checker palette. These are local native inverse, boot and rejection fixtures; no full free-certificate proof search, new theorem, universal compiler proof or new RL training is claimed.',
        timing_scope='Fresh process per observation. Cold solve includes table reading/pin checks, native oracle startup, complete domains, projection certificate synthesis, search, rollback and independent original/decorated point checks. Module import, Python startup, raw serialization and parent loading are outside solve clocks; complete worker stage clocks and one shared compile cost are also recorded.')
    (DOC/'native-wang-search-001.json').write_bytes(canonical(data)+b'\n');print('suite complete',data['seconds'],flush=True)
if __name__=='__main__':main()
