"""Prepare metadata-only scripts. No actual/scientific function calls."""
from pathlib import Path
S=Path('/private/tmp/gcts-first-admission-ROOT-source-20261017');P=Path('/private/tmp/gcts-callback-stage-ROOT-source-20261017')
s=(P/'direct_byte_preflight_v1.py').read_text().replace(str(P),str(S)).replace("P=Path('/private/tmp/gcts-head-gated-ROOT-source-20261017')","P=Path('/private/tmp/gcts-callback-stage-ROOT-source-20261017')")
s=s.replace("('intake','receiver_cases')","('intake','receiver_cases','family_engine')").replace('ROOT-callback-stage-direct-byte-preflight-v1','ROOT-first-admission-direct-byte-preflight-v1').replace('only intake/helper implementation pins changed','only intake/helper/engine diagnostic implementation pins changed')
(S/'direct_byte_preflight_v1.py').write_text(s)
s=(P/'prepare_actual_metadata_v1.py').read_text().replace(str(P),str(S))
s=s.replace('/private/tmp/gcts-head-gated-family-engine-peer-20261017/typed-Source-review-v7.json','/private/tmp/gcts-first-admission-journal-engine-peer-20261017/typed-Source-review-v8.json')
s=s.replace('/private/tmp/gcts-callback-stage-helper-peer-20261017/typed-Source-review-v1.json','/private/tmp/gcts-engine-milestone-helper-peer-20261017/typed-Source-review-v1.json')
s=s.replace('/private/tmp/gcts-callback-stage-inference-visible-ROOT-20261017','/private/tmp/gcts-first-admission-inference-visible-ROOT-20261017').replace('ROOT-callback-stage-receiver-visible-20261017-v1','ROOT-first-admission-receiver-visible-20261017-v1')
s=s.replace('Provider8, engine7, gate1 and every other scientific dependency remain raw-identical. Helper adds bounded provider/consumer/search diagnostics only. Science delegates remain unconditional beyond diagnostic caps.','Provider8, gate1 and all unchanged dependencies remain raw-identical. Engine8 adds four first root-family lifecycle diagnostic sites with owned immutable/COW record references; helper carries the observer endpoint. Diagnostic-erased engine AST equals parent; scientific calls and limits unchanged.')
s=s.replace('Root capture reads only exact builtin fixed fields and20 integer accounting counters before existing full-copy/hash work; it never changes provider value, admission or full scientific flow. Nonconforming diagnostic shape leaves null. Original20 native ticks guard capture; a slot is an unvalidated raw observation.','Root capture retains only a monotone four-slot prefix of existing engine-owned records without traversing/copying/hashing them. It adds four short phase labels. Existing bounded provider scalar capture is unchanged. Original20 native ticks guard all capture; raw records are never scientific admission.')
s=s.replace('Root failure writer remains captured-builtin failure55 only, no late scientific calls. Original legacy branch retained, V2 gets an explicit separate wire bound. New nested conditional phase parser allows caught callback unwinds; complete output counts come only from full returned records.','Root failure writer remains captured-builtin failure55 only, no late scientific calls. V3 preserves a whole-record prefix <=3MiB plus explicit captured headers/counts within the unchanged whole output bound; native55 TimeoutError propagates. The new saved parser joins exact34 phase labels, event-only raw schemas and current pins. Full positive output carries all4 raw slots under unchanged charged output bounds; no count from failure slots qualifies a result.')
s=s.replace('One bounded callback-stage inference diagnostic','One bounded first-admission milestone inference diagnostic').replace('same full original mathematical model/native limits','same full original mathematical model/native limits; four owned-record capture sites and bounded raw-prefix evidence only')
needle="for x in [*sources.values(),*inputs.values(),h['source_contract'],h['reader'],h['reader_source_contract']]:assert ref(x['path'])==x"
addition="""seam_path=Path('/private/tmp/gcts-first-admission-diagnostic-peer-20261017/typed-Source-review-v1.json')
seam=load(seam_path);assert seam['source_review_passed']is True and seam['source_only']is True and seam['scientific_calls']==0 and seam['scientific_acceptance']is False
assert seam['source']==ref('/private/tmp/gcts-first-admission-diagnostic-source-20261017/save_failure_diagnostic_v3.fragment.py')
"""
assert needle in s;s=s.replace(needle,addition+needle)
s=s.replace("saved_readout=dict(source=h['reader']", "diagnostic_seam_review=ref(seam_path),saved_readout=dict(source=h['reader']")
(S/'prepare_actual_metadata_v1.py').write_text(s)
for n in ('direct_byte_preflight_v1.py','prepare_actual_metadata_v1.py'):compile((S/n).read_text(),str(S/n),'exec',dont_inherit=True)
print('Prepared metadata scripts; compile without scientific evaluation.')
