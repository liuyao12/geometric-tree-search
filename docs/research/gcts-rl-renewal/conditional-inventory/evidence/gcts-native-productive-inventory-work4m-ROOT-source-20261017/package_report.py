"""Saved-data publication assembly only; never replays scientific helpers."""
from pathlib import Path
import hashlib
import json

S=Path('/private/tmp/gcts-native-productive-inventory-work4m-ROOT-source-20261017')
PUB=Path('/private/tmp/gcts-split-controls-publish-20261015')
ROOT=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
REL=Path('docs/research/gcts-rl-renewal/conditional-inventory')
OUT=PUB/REL
UI=Path('/private/tmp/gcts-native-productive-inventory-reader-source-20261017')
R=Path('/private/tmp/gcts-native-productive-inventory-work4m-ROOT-20261017')
R1=Path('/private/tmp/gcts-native-productive-inventory-ROOT-20261017')
BASE=Path('/private/tmp/gcts-native-inventory-startup-diagnostic-source-20261017/publication-task-manifest-v3.json')
def load(p):return json.loads(Path(p).read_bytes())
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def pin(p):
    b=Path(p).read_bytes();return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
old=load(OUT/'report-data.json');old_manifest=load(OUT/'evidence-manifest.json');base=load(BASE)
e=load(R/'ROOT-expanded-result-v1.json');payload=e['conditional_inventory'];p=payload['inventory'];comp=p['components']
d=load(R/'ROOT-disposition-v1.json');accept=load(R/'ROOT-source-ground-acceptance-v1.json')
assert p['status']=='CHECKED_CONDITIONAL_INVENTORY' and d['native_resources_qualified'] and len(p['qualified_records'])==4
assert accept['descriptors_qualified']==4 and accept['automatically_constructed_components']==2
sources=['gcts-native-component-composer-productive-source-20261017','gcts-native-component-composer-productive-peer-20261017','gcts-interface-coupled-miner-source-20261017','gcts-interface-coupled-miner-peer-20261017','gcts-native-productive-inventory-ROOT-source-20261017','gcts-native-productive-inventory-ROOT-20261017','gcts-native-productive-inventory-cases-source-20261017','gcts-native-productive-inventory-cases-peer-20261017','gcts-native-productive-inventory-cold-peer-20261017','gcts-native-productive-inventory-readout-peer-20261017','gcts-native-component-composer-work4m-source-20261017','gcts-native-component-composer-work4m-peer-20261017','gcts-native-productive-inventory-cases-work4m-source-20261017','gcts-native-productive-inventory-cases-work4m-peer-20261017','gcts-native-productive-inventory-work4m-ROOT-source-20261017','gcts-native-productive-inventory-work4m-ROOT-20261017','gcts-native-productive-inventory-work4m-cold-peer-20261017','gcts-native-productive-inventory-work4m-readout-peer-20261017','gcts-receiver-consumption-design-source-20261017']
extra=[]
for name in sources:
    source=Path('/private/tmp')/name
    for f in sorted(source.rglob('*')):
        if not f.is_file() or '__pycache__' in f.parts or any(x.startswith('live-bytes') for x in f.parts) or f.name.startswith('publication-task-manifest') or f.name.startswith('stage-paths'):continue
        assert not f.is_symlink()
        rel=Path('evidence')/name/f.relative_to(source);dest=OUT/rel;b=f.read_bytes();dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert dest.read_bytes()==b,dest
        else:dest.write_bytes(b)
        extra.append(dict(path=rel.as_posix(),source_path=str(f),**pin(dest)))
components=[]
for index,c in enumerate(comp['components']):
    slot='open' if c['input_ports'] else 'closed'
    occupied={v['tile']['placement_key']['translation'][1] for v in c['members']}
    rows=[]
    for v in c['members']:
        tile=v['tile'];pre=tile['base_tile']['placement_key']['type_preimage'];row=tile['placement_key']['translation'][1];w=pre['primitive_witness'];rule=w['rule']
        english={'axiom':'Introduce the declared successor-addition axiom.','generalize':'Add a universal quantifier for a variable absent from the axiom. This step is valid and redundant.','mp':'Apply modus ponens to the selected axiom and the required implication. The output remains conditional while the implication is unfilled.'}[rule]
        rows.append({'row':row,'rule':rule,'formula':w['formula'],'english':english,'tile':tile,'premises':[{'row':row+offset,'formula':formula,'internal':row+offset in occupied} for offset,formula in zip(pre['ordered_offsets'],pre['ordered_premise_formulas'])]})
    records=[]
    for q in p['qualified_records']:
        if q['component_index']!=index:continue
        record=q['record'];abstract=record['fragment_generalization'] is not None
        summary=('The FORMULA parameter occurs in the open implication and exposed output; this source instance binds it to contradiction.' if slot=='open' else 'The axiom is abstracted as a FORMULA parameter, without an open input/output connection.') if abstract else 'Literal descriptor of this exact connected fragment, expanded and checked again against the original root.'
        summary_record={'field_selection':'Complete mined descriptor plus selected qualification fields; complete expansion/check/native packets are retained in the linked full evidence.','descriptor':record['descriptor'],'family_id':record['family_id'],'substitution':record['substitution'],'source_port_bindings':record['source_port_bindings'],'fragment_generalization':record['fragment_generalization'],'costs':record['costs'],'status':q['status'],'source_roundtrip':q['source_roundtrip'],'rebound_roundtrip':q['rebound_roundtrip'],'source_check_status':q['source_check']['status'],'check_status':q['check']['status'],'adaptation_status':q['adaptation']['status'],'local_member_membership_checked':q['adaptation']['local_member_membership_checked'],'local_point_union_checked':q['adaptation']['local_point_union_checked']}
        records.append({'kind':'Formula abstraction' if abstract else 'Literal descriptor','summary':summary,'record':summary_record})
    components.append({'slot':slot,'component_id':c['component_id'],'label':'Open cluster' if slot=='open' else 'Closed comparison','description':'Axiom and modus ponens form a connected cluster around an unfilled implication. The final line is conditional.' if slot=='open' else 'The axiom and a vacuous generalization form the closed comparison cluster. It is redundant.','rows':rows,'open_inputs':c['input_ports'],'records':records,'alias':json.dumps(rows[0]['formula'],separators=(',',':'),ensure_ascii=False)})
assert [v['slot'] for v in components]==['closed','open']
attempts=[]
for v in old['attempts']:
    attempts.append(dict(v,outcome='one source cluster checked' if v['disposition']['status']=='CHECKED_CONDITIONAL_INVENTORY' else 'unknown'))
attempts.extend([{'label':'Closed/open slots; construction cap one million','outcome':'unknown at construction work cap','disposition':load(R1/'ROOT-disposition-v1.json')},{'label':'Closed/open slots; construction cap four million','outcome':'both source clusters checked','disposition':d}])
def link(label,folder,name):return [label,'evidence/'+folder+'/'+name]
links=[link('Current narrow source-instance acceptance',R.name,'ROOT-source-ground-acceptance-v1.json'),link('Current complete expanded evidence',R.name,'ROOT-expanded-result-v1.json'),link('Current saved disposition',R.name,'ROOT-disposition-v1.json'),link('Current frozen plan',R.name,'ROOT-plan-v1.json'),link('Smaller construction allowance: complete unknown record',R1.name,'ROOT-expanded-result-v1.json'),link('Current cold caller Source and protocol',S.name,'Source-contract-v2.json'),link('Current native cluster composer',sources[10],'native_conditional_component_composer_v3.py'),link('Current staged inventory checks',sources[12],'native_productive_inventory_cases_v4.py'),link('Interface-based family miner',sources[2],'receptor_family_miner_v3.py'),link('Independent composer Source review',sources[11],'typed-Source-review-v3.json'),link('Independent staged-check Source review',sources[13],'typed-Source-review-v4.json'),link('Independent miner Source review',sources[3],'typed-Source-review-v3.json'),link('Current integration review',sources[16],'typed-Source-review-v2.json'),link('Current saved-reader review',sources[17],'typed-Source-review-v2.json'),link('Next receiver inference design: Source only',sources[18],'recommendation-v1.json'),['Complete raw evidence byte manifest','evidence-manifest.json']]
for label,url in old['evidence_links']:
    if [label,url] not in links:links.append(['Earlier record: '+label,url])
data={'schema':'ROOT-native-productive-inventory-reader-data-v1','status_text':'Two source clusters qualified · one has an open receptor','disposition':d,'launch_ns':load(R/'NPI-external-v1/native-terminal.json')['caller_launch_began_ns'],'components':components,'display_order':[1,0],'boundary_channel4':[v for v in payload['marking']['boundary_m_values'] if v[0][0]==4] if 'boundary_m_values' in payload['marking'] else None,'marking_counts':accept['added_marking_counts_on_complete_exposed_cursor_prefixes'],'attempts':attempts,'evidence_links':links,'run_details':{'scope':p['scope'],'work':p['work'],'composer_work':comp['work'],'slot_availability':comp['slot_availability'],'descriptors_qualified':4,'alternative_components':2,'distinct_placements_across_alternatives':3,'global_type_census_count':len(p['census']),'source_substitutions_only':True,'open_input_occupied':False,'open_input_fact_accepted':False,'interface_coupled_parameters':1,'flags':p['flags'],'counts_scope':'Full exposed cursor prefixes; never a global degree/exhaustion certificate.','whole_evidence':'evidence/'+R.name+'/ROOT-expanded-result-v1.json'},'rows':components[0]['rows'],'records':components[0]['records'],'result_title':'Closed and open source instances passed fresh checks.','result_text':'Four descriptors describe two alternative clusters, including a shared formula parameter at an open interface.','reader_intro':'The closed comparison is shown below; the current reader also offers the open cluster.'}
# The marking definition uses its established explicit root assignments.
if data['boundary_channel4'] is None:
    data['boundary_channel4']=[v for v in comp['root']['state']['m'] if v[0][0]==4]
assert data['boundary_channel4']==[[[4,0],0]]
dump(OUT/'report-data.json',data)
for name in ('reader.html','reader.js','reader.css'):(OUT/name).write_bytes((UI/name).read_bytes())
manifest_rows={v['path']:v for v in old_manifest['files']}
for v in extra:manifest_rows[v['path']]=v
dump(OUT/'evidence-manifest.json',{'schema':'ROOT-native-productive-inventory-evidence-manifest-v1','raw_bytes_preserved':True,'scientific_replay':False,'files':[manifest_rows[k] for k in sorted(manifest_rows)],'shared_existing_files':base['shared_existing_files']})
idx=PUB/'docs/research/gcts-rl-renewal/index.html';text=idx.read_text();start=text.index('<section class="panel" id="conditional-inventory">');end=text.index('</section>',start)+len('</section>')
panel=r'''<section class="panel" id="conditional-inventory"><p class="eyebrow">AUTOMATIC CONDITIONAL INVENTORY · 17 OCTOBER</p><h2>An open receptor and a shared formula parameter.</h2><p>The composer now finds a closed cluster and an axiom–modus-ponens cluster with an unfilled implication. All \(4\) descriptors passed fresh checks at their source instances in \(5.64\) native seconds. One formula parameter connects the open input to the output; its source substitution is contradiction, conditional on the missing premise. No contradiction or new target theorem has been proved. The frozen added marking rejected \(1\) of \(29\) exposed candidates; reuse at a different receiver, trained RL and a practical search advantage remain unfinished.</p><p><a href="conditional-inventory/reader.html?v=npi1#reader">Inspect both clusters, the missing receptor, colored point markings and all five attempts</a>.</p></section>'''
idx.write_text(text[:start]+panel+text[end:])
prev=PUB/'docs/research/gcts-rl-renewal/checked-tile-reuse/reader.html';text=prev.read_text();start=text.index('  <section id="inventory-update">');end=text.index('</section>',start)+len('</section>')
prev.write_text(text[:start]+'  <section id="inventory-update"><h2>New: an automatically constructed open cluster</h2><p><a href="../conditional-inventory/reader.html?v=npi1#reader">Inspect a missing implication receptor and its shared formula parameter.</a> Both alternative clusters passed checks at their source instances. Reuse at another receiver and a search advantage remain unfinished.</p></section>'+text[end:])
owned={v['path'] for v in base['files']}
for f in OUT.rglob('*'):
    if f.is_file():owned.add(f.relative_to(PUB).as_posix())
for f in (idx,prev):owned.add(f.relative_to(PUB).as_posix())
rows=[]
for path in sorted(owned):rows.append(dict(path=path,**pin(PUB/path)))
for v in base['shared_existing_files']:assert pin(PUB/v['path'])=={k:v[k]for k in ('bytes','sha256')}
dump(S/'publication-task-manifest-v1.json',{'schema':'ROOT-productive-inventory-publication-task-manifest-v1','files':rows,'shared_existing_files':base['shared_existing_files']})
(S/'stage-paths.nul').write_bytes(b'\0'.join(v['path'].encode()for v in rows)+b'\0')
root_index=ROOT/'docs/research/gcts-rl-renewal/index.html';assert pin(root_index)['sha256']=='d04878220b6c43b16bbc1ff6cd17d24d824e2c3049a2b47600f0e26eec0cd770'
# Sync the task-owned reader directory; preserve the separately dirty Root index.
old_pins={v['path']:{k:v[k]for k in ('bytes','sha256')}for v in base['files']}
for f in OUT.rglob('*'):
    if not f.is_file():continue
    path=f.relative_to(PUB);dest=ROOT/path;b=f.read_bytes()
    if dest.exists() and dest.read_bytes()!=b:assert pin(dest)==old_pins[path.as_posix()],dest
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
print(json.dumps({'task_files':len(rows),'shared_files':len(base['shared_existing_files']),'published_evidence_files':len(manifest_rows),'report_data_bytes':(OUT/'report-data.json').stat().st_size,'total_bytes':sum(v['bytes']for v in rows)+sum(v['bytes']for v in base['shared_existing_files']),'root_index_preserved':True}))
