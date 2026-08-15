#!/usr/bin/env python3

from materials_gcts_iqc_action_graph_corpus import submacro_edge_records
from materials_gcts_iqc_action_graph_corpus_benchmark import evaluate


result = evaluate()
corpus = result.corpus
assert len(corpus.patches) == 6
assert corpus.training_atoms == 887
assert corpus.threshold_ratio == 15 / 21
assert corpus.maximum_waves == 5
assert corpus.maximum_accepted_per_wave == 40
assert corpus.total_actions == len(submacro_edge_records(corpus))
assert corpus.total_actions > 0
assert corpus.corpus_digest == "8645b480d2e1caa1a620d3541df8b37a06213b27707e085bdb0d62bd70d8dfe8"
assert not corpus.target_labels_stored
assert not corpus.target_used_during_execution
assert not corpus.family_phi_cell_stored
assert result.every_patch_disjoint_from_training
assert result.every_patch_pair_disjoint
assert not result.corpus_filtered_by_posthoc_target
assert result.scoring_performed_after_all_executions
assert set(result.exact_patches).isdisjoint(result.noisy_patches)
assert len(result.exact_patches) + len(result.noisy_patches) == 6

print("IQC target-free action-graph corpus: all assertions passed")
