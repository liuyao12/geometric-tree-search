"""The unchanged point model applied after audited structural pruning.

All C/G/I1/I2 candidate placements inside the retained grammar are generated.
The separate fixed-point certificate proves that omitted full-grammar edges
cannot occur in finite strict-prior proof words. Native registry hashes must
bind every actual retained local definition, never an unknown placeholder.
"""
import hashlib
from certificate_boundary_search import canonical
from induction_receptors_points import Model as Base

class Model(Base):
    def __init__(self,spec,catalog,admission):
        if admission.get('admission_audit_status')!='passed_complete_reachable_native_admission' or admission.get('pilot_audit_status')!='passed_preparation_native_replay_only':raise ValueError('complete independent native admission required')
        actual={d['name']:hashlib.sha256(canonical(d)).hexdigest() for d in catalog['definitions']}
        if actual!=admission['complete_definition_sha256'] or admission['pruning_witness_sha256']!=catalog['structural_pruning']['witness_sha256']:raise ValueError('complete exact registry/pruning binding')
        super().__init__(spec,catalog,admission)
    def record(self):
        value=super().record();value.update(structural_pruning=self.compiled['structural_pruning'],scope='Every exact C/G/I1/I2 root, retained interface and strict-prior input source is generated, with complete frontier graph and unchanged dead/forced/earliest-generation/fallback/rollback. Full unpruned finite grammar is preserved separately; a complete independently replayed fixed-point witness proves omitted edges cannot occur in any strict-prior finite proof word. High-level point adaptation, not primitive-square Wang occupancy or full-FOL completeness. No RL.')
        return value
