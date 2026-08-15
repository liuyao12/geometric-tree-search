#!/usr/bin/env python3

from materials_gcts_iqc_clean_training_action_corpus import (
    clean_submacro_edge_records)
from materials_gcts_iqc_clean_training_action_corpus_benchmark import evaluate


result = evaluate()
corpus = result.corpus
assert len(corpus.patches) == 5
assert corpus.training_atoms == 887
assert corpus.seed_radius == 5.
assert corpus.public_boundary_radius == 7.
assert corpus.total_exact_actions == len(clean_submacro_edge_records(corpus))
assert corpus.total_exact_actions > 0
assert corpus.known_training_labels_used_for_exact_trace_selection
assert not corpus.heldout_patch_atoms_or_labels_used
assert not corpus.target_correctness_labels_stored
assert corpus.semantic_descriptors_train_only
assert len(corpus.prototypes) == corpus.frozen_prototypes
assert len(corpus.productions) == corpus.frozen_productions
assert result.seed_domains_inside_public_domains
assert result.every_public_domain_inside_training
assert result.exact_actions_only
assert not result.heldout_deployment_patches_used

print("clean IQC training action corpus: all assertions passed")
