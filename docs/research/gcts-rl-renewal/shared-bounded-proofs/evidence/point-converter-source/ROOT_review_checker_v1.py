"""Source/AST and small review metadata only; no imported scientific functions."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
OTHER = BASE / 'shared-bounded-point-board-independent-source-20261015'

def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

source = OTHER / 'independent_word_point_board_checker_v1.py'
contract = OTHER / 'Source-contract-v1.json'
assert pin(source)['sha256'] == '99b3bdc393d4fbdc4bddf08b362ca58c80a06a129908e854b0303e495303c18d'
assert pin(contract)['sha256'] == 'f906431ebe88084bb18ee537c388176e8a2110312cfa6a69792738c9a23a9ae9'
tree = ast.parse(source.read_bytes())
compile(tree, str(source), 'exec')
value = {
    'schema': 'ROOT-bounded-word-point-board-checker-typed-Source-review-v1',
    'scope': 'Exact positive translated point-board projection only',
    'author_identity': '/root/arithmetic_induction',
    'reviewer_identity': '/root',
    'authorship_disclosure': 'Root authored the untrusted converter, not this independently written checker. This is a checker Source review, not independent logical or resource acceptance.',
    'source': pin(source), 'source_contract': pin(contract),
    'source_only': True, 'source_review_passed': True,
    'scientific_calls': 0, 'scientific_acceptance': False,
    'all_checks_passed': True,
    'checks': [
        'Read the entire checker and contract; AST parses and compiles without executing the Source.',
        'Private original word/height/epoch authority; no converter imports or calls.',
        'Exact six-rule field sets, typed strict-prior source references and nonempty first zero-port row.',
        'Independent direct absolute-row padding and source-index shifts preserve the original complete word.',
        'Whole prototype preimages, literal canonical formula values, port order and relative offsets are reconstructed.',
        'Every local/global t/m value, fixed boundary, required point and packet field is compared recursively with exact builtin types.',
        'Actual compared positive support is reaccumulated; each required point totals one with no outside support.',
        'All active/fixed mark occurrences, including agreeing repeated reads, participate in literal union checks.',
        'Selected placement identities are unique; repeated digest IDs must retain identical whole preimages.',
        'Receipt returns the rebuilt padded commands for separate bounded membership and unchanged1717 original-context checking.',
        'Callback exceptions propagate; no Source execution, plans, clocks, process control or output behavior is hidden in this module.',
        'The correspondence argument is conditional on selected inventory validity and complete full-value encodings; no graph/count/scheduler authority follows.'
    ],
    'external_gates': [
        'Authenticate exact original declaration/profile/word and current Sources in a fresh cold caller.',
        'Check every padded command in selected bounded language and whole padded word against the original closed target with unchanged1717.',
        'Run meaningful malformed/conflicting packet controls within an authorized actual.',
        'Close complete output/wire/native-terminal/resource measurements separately.'
    ],
    'not_accepted': ['automatic_discovery', 'logical_proof', 'complete_inventory_counts', 'GCTS_search', 'trajectory', 'RL', 'native_Wang_palette', 'resource_fit']
}
out = HERE / 'ROOT-point-checker-Source-review-v1.json'
with out.open('x') as stream:
    json.dump(value, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(pin(out)))
