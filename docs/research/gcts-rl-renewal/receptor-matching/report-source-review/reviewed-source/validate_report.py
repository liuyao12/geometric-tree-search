"""Validate display projections, frozen file routes and one-panel publication scope."""
import gzip
import hashlib
import json
import os
import subprocess
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from report_evidence import ROOT, PUB, PREFIX, DEST, pin, load

HERE=Path(__file__).resolve().parent
MAIN='docs/research/gcts-rl-renewal/index.html'


class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=[]

    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if 'id' in values:self.ids.append(values['id'])
        if tag=='a' and 'href' in values:self.links.append(values['href'])


def main():
    manifest=load(HERE/'task-files.json')
    paths={entry['path'] for entry in manifest}
    assert len(paths)==len(manifest)
    assert all(path==MAIN or path.startswith(PREFIX) for path in paths)
    for entry in manifest:
        assert pin(ROOT/entry['path'])=={k:entry[k] for k in ('sha256','bytes')},entry['path']
    bindings=load(DEST/'source-input-bindings.json');cache={}
    for entry in bindings:
        base=ROOT if entry['published_path'].startswith(PREFIX) else PUB
        route=base/entry['published_path']
        if entry.get('archive_member'):
            if str(route) not in cache:cache[str(route)]=zipfile.ZipFile(route)
            raw=cache[str(route)].read(entry['archive_member'])
            observed=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        else:observed=pin(route)
        assert observed=={k:entry[k] for k in ('sha256','bytes')},entry['path']
    for archive in cache.values():archive.close()
    origins=load(DEST/'origins.json')
    for entry in origins:
        assert pin(ROOT/entry['path'])==pin(ROOT/entry['origin'])=={k:entry[k] for k in ('sha256','bytes')}
    selected=load(HERE/'terminal-selection.json')
    phase=ROOT/selected['producer_folder']
    acceptance=load(ROOT/selected['independent_result'])
    assert acceptance['status']==selected['independent_result_status']
    assert acceptance['observation_verdicts']==selected['observation_verdicts'],'audit acceptance provenance'
    plan=load(phase/'search-plan-v1.json')
    outcome=load(phase/'search-outcome-v1.json')
    life=load(phase/'search-lifetime-v1.json')
    assert selected['all_owned_handles_terminal'] and life['worker_terminal_reaped_confirmed']
    assert life['status']=='passed_automatic_primitive_geometry_full_lifetime'
    assert outcome['target_search_observations']==2
    assert outcome['authored_words_used_as_hints']==outcome['native_queries']==0
    assert outcome['new_RL_training'] is False
    model_pin=next(entry for entry in plan['inputs'] if entry['role']=='primitive_model')
    with gzip.open(ROOT/model_pin['path'],'rt') as stream:model=json.load(stream)
    visual=load(DEST/'visual-data.json')
    recipient_models=[entry for entry in model['models'] if entry['height']==24]
    assert len(recipient_models)==1
    assert visual['formula_codes']==model['formula_codes']
    assert visual['recipes']==[{k:recipe[k] for k in ('id','primitive_witness','ordered_premise_formulas')} for recipe in model['recipes']]
    assert visual['hypotheses']==recipient_models[0]['context']['ordered_local_premises']
    assert visual['target']==model['formula_codes'][54]
    assert len(visual['observations'])==len(outcome['observations'])==2
    event_counts=[];maximum_rows=[]
    for projected,saved in zip(visual['observations'],outcome['observations']):
        with gzip.open(ROOT/saved['result']['path'],'rt') as stream:raw=json.load(stream)
        verdict=selected['observation_verdicts'][saved['id']]
        augmented=dict(raw,id=saved['id'],independent_certificate_accepted=verdict['certificate_accepted'],independent_trace_accepted=verdict['trace_accepted'],independent_scope=verdict['scope'])
        assert projected==augmented,'viewer changed original observation fields'
        assert raw['point_certificate'] is None and raw['decoded_certificate'] is None
        assert verdict['certificate_accepted'] is False
        assert raw['status']=='unknown_search_budget' and raw['attempts']==128
        assert raw['root_restored'] is True
        assert raw['initial_state']==raw['terminal_state']
        assert raw['active_cluster_descriptors']==raw['authored_words_used_as_hints']==raw['native_queries']==0
        event_counts.append(len(raw['events']))
        maximum_rows.append(max(len(event['state']['projection']['graph']['order']) for event in raw['events']))
    assert event_counts==[1168,1280]
    raw=(DEST/'reader.html').read_text();parser=Links();parser.feed(raw)
    assert len(parser.ids)==len(set(parser.ids))
    assert {'observation','trace-event','proof-view','trace-view','formula-layer','reference-layer','reader'}<=set(parser.ids)
    checked=[]
    for href in parser.links:
        if href.startswith(('https:','http:')):continue
        name=href.split('#')[0].split('?')[0]
        route=Path(os.path.normpath(str(DEST/name))) if name else DEST/'reader.html'
        if name.endswith('/'):route=route/'index.html'
        relative=str(route.relative_to(ROOT))
        route=ROOT/relative if relative in paths or relative.startswith(PREFIX) else PUB/relative
        assert route.is_file(),href
        if href.startswith('#'):assert href[1:] in parser.ids,href
        checked.append(href)
    baseline=subprocess.check_output(['git','show','a4adb7b113338e6b8753b880356954b6a26d2086:'+MAIN],cwd=PUB).decode()
    actual=(ROOT/MAIN).read_text()
    start=actual.index('<section class="panel" id="receptor-matching">')
    end=actual.index('<section class="panel" id="automatic-geometry">',start)
    restored=(actual[:start]+actual[end:]).replace('RESEARCH NOTEBOOK · 107','RESEARCH NOTEBOOK · 106',1)
    assert restored==baseline,'main edit exceeds one panel and notebook counter'
    result=dict(status='passed_exact_report_routes_projection_links_and_baseline',task_files=len(manifest),source_bindings=len(bindings),origins=len(origins),archive_routes=sum(bool(entry.get('archive_member')) for entry in bindings),local_links=len(checked),observations=2,saved_events=event_counts,maximum_saved_rows=maximum_rows,accepted_certificates=0,original_observation_fields_byte_value_preserved=True,main_scope='One additive panel, notebook106 to107, exact committed a4adb7b1 baseline.',scientific_execution=False,browser_math_and_interactions='pending live validation')
    (HERE/'local-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
