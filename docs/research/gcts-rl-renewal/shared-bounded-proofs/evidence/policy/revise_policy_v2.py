"""Explicit finite fresh-name profile boundary, before implementation or execution."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
old=ROOT/'ROOT-profile-choice-v1.json'
raw=old.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='09ca475758de1ef3463b5c33fe1606ef2812090b4f0361423db7d3210163a3df'
policy=json.loads(raw)
policy['schema']='ROOT-shared-bounded-six-rule-language-policy-v2'
policy['profile_name']='shared-bounded-six-rule-B12-N44-v2'
policy['supersedes_unactivated_policy']={'path':str(old),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
policy['syntax']['fresh_exhaustion']='A primitive whose exact capture-safe substitution requires a fresh suffix32 or greater is explicitly OUT_OF_PROFILE_FRESH_NAMESPACE. A complete literal name-set census must justify this exclusion. No alpha merging, alternative spelling or fresh-name extension is allowed. Time, visit, depth or other computation exhaustion is UNKNOWN membership, never evidence of this exclusion; propagate it.'
policy['syntax']['input_gate']='Validate every named axiom, every original Gamma occurrence and the target against the complete scoped syntax and uniform bounds before producing a language object. An out-of-profile input rejects this profile for that input; it is never silently dropped. This gate does not prove the target or any non-axiom formula.'
policy['primitive_relation']['membership_outcomes']='MEMBER with exact witness/premises/preimage; explicit OUT_OF_PROFILE with a complete syntactic or fresh-namespace reason; or UNKNOWN if computation/resource evidence is incomplete. Heuristics and budget failures cannot return OUT_OF_PROFILE.'
out=ROOT/'ROOT-profile-choice-v2.json'
with out.open('x') as handle:json.dump(policy,handle,indent=2,sort_keys=True);handle.write('\n')
result=out.read_bytes()
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(result).hexdigest(),'bytes':len(result)}))
