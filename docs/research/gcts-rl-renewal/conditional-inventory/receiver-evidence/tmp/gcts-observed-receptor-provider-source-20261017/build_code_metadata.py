"""Author Source bytes/AST only; no project evaluation."""
import ast,hashlib,json
from pathlib import Path
H=Path('/private/tmp/gcts-observed-receptor-provider-source-20261017');P=Path('/private/tmp/gcts-receptor-transfer-provider-source-20261017/receptor_transfer_physical_provider_v3.py')
a=P.read_bytes();assert hashlib.sha256(a).hexdigest()=='23daab1085b7ddc04e447f069b2ceb0271ad307abab81ff560549f8b346460aa'
s=a.decode();edits=[]
def change(label,o,n):
 global s
 assert s.count(o)==1,(label,s.count(o));i=s.index(o);edits.append({'label':label,'start':i,'old':o,'new':n});s=s[:i]+n+s[i+len(o):]
change('own_VERSION',"VERSION = 'receptor-family-visible-receptor-transfer-provider-v3'","VERSION = 'receptor-family-observed-receptor-transfer-provider-v4'")
change('report_schema',"RESULT_SCHEMA = 'receptor-family-receptor-transfer-provider-v1'","RESULT_SCHEMA = 'receptor-family-observed-receptor-transfer-provider-v2'")
change('miner_VERSION',"MINER_VERSION = 'receptor-family-primitive-DAG-miner-v2-connected-cut-selection'","MINER_VERSION = 'receptor-family-primitive-DAG-miner-v3-interface-coupled-catalogue'")
change('new_public_dependency_tags',"PRODUCER_VERSION = 'receptor-family-typed-expander-v1'", "PRODUCER_VERSION = 'receptor-family-typed-expander-v1'\nPRODUCER_IMPLEMENTATION = 'receptor-family-observed-subset-inference-v2'\nRESIDUAL_POLICY_VERSION = 'receptor-family-residual-host-binding-prefix-v1'\nMEMBERSHIP_VERSION = 'shared-bounded-six-rule-language-v2'\nINFERENCE_BINDING_POLICY = 'EMPTY_PROBE_THEN_THEORY_NAMES_INTERLEAVED_V1'\nLITERAL_BINDING_POLICY = 'EXPLICIT_MINED_ORIGIN_ENVIRONMENT_V1'")
change('bounded_plan_prefix_type',"class _Unfinished(Exception):\n    pass\n", "class _Unfinished(Exception):\n    pass\n\n\nclass _AssignmentPrefix(_Unfinished):\n    pass\n")
change('plan_cap_does_not_discard_completed_plan',"raise _Unfinished('OWN_PHYSICAL_ROW_TRIAL_PREFIX')","raise _AssignmentPrefix('OWN_PHYSICAL_ROW_TRIAL_PREFIX')")
change('preflight_original_membership_module',"def _preflight(expansion, assignment, language, base, point, state_parts, names, work):","def _preflight(expansion, assignment, language, base, point, membership_module, state_parts, names, work):")
change('completed_exact_native_nonmembership_is_scoped',"        # Native rejection is NOT caught as an advisory mismatch.\n        membership = language.primitive(witness, premises)\n", "        # Only this original module's completed definite rule exclusion may\n        # reject the current advisory binding. Native/unknown/guard errors escape.\n        try:\n            membership = language.primitive(witness, premises)\n        except membership_module.OutsideLanguage as error:\n            if type(error) is not membership_module.OutsideLanguage:raise\n            memberships.append({'node_id': node['id'], 'witness': witness,\n                'ordered_premise_formulas': premises, 'status': 'OUTSIDE_LANGUAGE',\n                'reason': work.copy(error.reason), 'evidence': work.copy(error.evidence),\n                'scope': 'THIS_PROPOSED_MEMBER_BINDING_ONLY', 'pruning_accepted': False})\n            result.update(status='NATIVE_MEMBER_EXCLUDED', reason='COMPLETED_ORIGINAL_MEMBER_EXCLUSION',\n                          node_id=node['id'], row=row)\n            return result\n")
i=s.index('def build_family_batch(');change('observed_subset_mode_independent_planning_and_full_fresh_qualification',s[i:],(H/'new_build_body.txt').read_text())
b=s.encode();t=ast.parse(b);compile(b,'<observed-receptor-provider-Source>','exec',dont_inherit=True)
back=s
for e in reversed(edits):
 i=e['start'];assert back[i:i+len(e['new'])]==e['new'];back=back[:i]+e['old']+back[i+len(e['new']):]
assert back.encode()==a and ast.dump(ast.parse(back),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
p=H/'observed_receptor_physical_provider_v4.py'
with p.open('xb')as f:f.write(b)
(H/'author-code-delta.json').write_text(json.dumps({'edits':edits},sort_keys=True,indent=2)+'\n')
print(json.dumps({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'edits':len(edits)},sort_keys=True))
