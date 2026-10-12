"""Metadata-only record of source inspection; no producer/scientific imports."""
import ast
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PRODUCER=ROOT/'.gcts-active/fixed-family-transfer-source-v1-20261012'


def pin(path):
    path=Path(path).resolve();h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(65536),b''):h.update(chunk)
    return dict(path=str(path),sha256=h.hexdigest(),bytes=path.stat().st_size)


def main():
    began=time.perf_counter();plan=json.loads((PRODUCER/'preparation-plan-v1.json').read_text())
    checked={};asts=[]
    for group in ('sources','inputs','preserved_files'):
        for item in plan[group]:
            path=(ROOT/item['path']).resolve();actual=checked.setdefault(str(path),pin(path))
            if (actual['sha256'],actual['bytes'])!=(item['sha256'],item['bytes']):raise ValueError('exact prior pin mismatch')
    for item in plan['sources']:
        path=ROOT/item['path'];tree=ast.parse(path.read_text(),filename=str(path))
        asts.append(dict(source=pin(path),AST_nodes=sum(1 for _ in ast.walk(tree))))
    archive=PRODUCER/'sources-v1.zip';members=[]
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            data=z.read(name);actual=pin(ROOT/name)
            if actual['sha256']!=hashlib.sha256(data).hexdigest() or actual['bytes']!=len(data):raise ValueError('archive exact source mismatch')
            members.append(dict(name=name,sha256=actual['sha256'],bytes=len(data)))
    for role in ('binary','process_metadata'):
        item=plan['runtime'][role];actual=pin(item['path'])
        if actual!=item:raise ValueError('exact runtime/observer bytes')
    review=dict(status='PASS_prospective_source_only_fresh_transfer_preparation_review',
        preparation_plan=pin(PRODUCER/'preparation-plan-v1.json'),source_archive=pin(archive),
        source_coverage='All10 functional/metadata sources read in full; changed-context/compiler, full preparation and deferred search/register/finalizer contracts inspected without executing helpers.',
        parsed_sources=asts,archive_members=members,unique_raw_byte_pins=len(checked),mismatches=0,
        no_blocking_source_defect_found=True,
        findings=[
            'Complete217formula/229recipe palette and exact original/new Gamma are source-checked; all226 non-assumption records retain identity and provenance. All3 assumption recipe preimages/IDs bind fresh context, even unchanged formulas.',
            'Source primitive authority is inactive and theory-bound; Gamma does not occur in that authority payload. Fresh graph context/source epoch and full-placement/body/group identities are reconstructed. Prior positive audit is provenance, not new acceptance.',
            'All171 source bodies are transported from complete compact projection; canonical local aliases never become recipient seeds. Whole171+29241 grammar uses all root/output Cartesian bindings and retains ordered multiplicity, explicit possibly non-last conclusions, exact full-key sharing and immutable priority epoch.',
            'Preparation emits the complete compiled payload, full conditional body registry, all group records, whole24-row initial-domain hashes and complete census; no Controller/Executor/target search/checker/native/training call in preparation worker.',
            'Three future lanes share the generalized literal DFS and one Controller resync; base/fixed have empty descriptors, whole pool uses complete fresh groups. Graph degrees, forced/dead/earliest ordering and full fallback remain primitive. UNKNOWN children restore without exclusion; fully exhausted children alone authorize parent exclusions.',
            'Future metadata-only search finalizer requires separately accepted fresh static result/lifetime and exact ROOT terminal receipts; no placeholder gate pins. Separate search review/activation and trace/logical positive acceptance remain required.',
            'Source output paths are exclusive and versioned; owner refuses prior outputs, monitors own child, kills/waits on supervisory failure and preserves missing-result/partial gates as UNKNOWN. Complete prep60/55/50s and512MiB producer estimates are prospective.'],
        caveats=[
            'Source review is not new model/license/body/pool runtime acceptance. New independent static checking must pass before search.',
            'Preparation and search owner peak estimates omit simultaneous ps RSS and use retrospective child peaks; no OS hard cap or strict aggregate host upper bound. Root full outer-process timing/receipt serialization is additional.',
            'Canonical single/pair embeddings are incomplete advice; the full primitive universe is the complete fallback. Existing171 authored/certified source interfaces are not newly discovered lemmas.',
            'This is within-library changed-premise recipient transfer only. Native/compiler/shared request-independent universal Wang correspondence remains open.'],
        metadata_review_seconds_before_receipt_write=time.perf_counter()-began,
        metadata_kernel_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        scientific_imports_model_helpers_checkers_fixtures_search_native_training=0,
        activation_written=False,owner_run=False,ROOT_sole_actual_owner=True)
    with (HERE/'preparation-source-review-v1.json').open('x') as stream:
        json.dump(review,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(review=pin(HERE/'preparation-source-review-v1.json'),unique_raw_byte_pins=len(checked),scientific_execution=False)))


if __name__=='__main__':main()
