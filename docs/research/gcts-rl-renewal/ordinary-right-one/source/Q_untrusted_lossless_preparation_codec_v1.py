"""UNEXECUTED allocation-only codec for the untrusted full-Q producer child.

No old worker imports, paths, model regeneration or mathematical acceptance.
ROOT authenticates whole fixed buffers/EOF and owns all process/budget custody.
Decode first, drop the child caller's raw-buffer reference, then parse once.
Actual fit and parser controls remain unmeasured. Finite metadata floats are
preserved, including signed zero; semantic AST/ports retain their literal wire.
"""
import hashlib
import json
import math

VERSION = 'Q-untrusted-lossless-shared-syntax-preparation-codec-Source-v1'
PREPARATION_SHA256 = '0321a462025357d188793bd45a44670adc20776e9ba30574049d77a8b5935d3a'
PREPARATION_BYTES = 38376960


def need(ok, message):
    if not ok:
        raise ValueError(message)

def syntax_array(value):
    # Storage recognizer only: no signature, capture, rule or grammar decision.
    # Unknown/malformed shapes are retained unchanged for the independent audit.
    if type(value) is not list or not value or type(value[0]) is not str:
        return False
    lengths={'var':2,'fun':3,'bot':1,'eq':3,'pred':3,'all':3,'not':2,'imp':3,'and':3,'or':3}
    return value[0] in lengths and len(value)==lengths[value[0]]

def syntax_atom_key(value):
    # Python False==0 and 0.0==-0.0 must never merge different JSON values/types.
    if value is None:return ('null',)
    if type(value) is bool:return ('bool',value)
    if type(value) is int:return ('int',value)
    if type(value) is float:
        if not math.isfinite(value):return None
        return ('float',value.hex())
    if type(value) is str:return ('str',value)
    return None

def share_syntax_value(value, memo, identities):
    """Value-preserving sharing inside a recognized literal syntax tree only.

    Keys retain every typed scalar and every ordered list child. Returned wire
    nodes remain actual lists, never tuples/codes/alpha-equivalence classes.
    Dictionaries or unexpected objects are not interned. Record/occurrence,
    port arrays, recipe and model identities remain separate containers.
    """
    def tree(node):
        if type(node) is not list:
            key=syntax_atom_key(node)
            return node,key
        old=identities.get(id(node))
        if old is not None and old[0] is node:
            return node,old[1]
        children=[];keys=[]
        for child in node:
            shared,key=tree(child)
            if key is None:
                return node,None
            children.append(shared);keys.append(key)
        key=('list',tuple(keys))
        if key in memo:
            return memo[key],key
        node[:]=children
        memo[key]=node;identities[id(node)]=(node,key)
        return node,key
    if type(value) is not list:
        # Dictionary children already passed through object_pairs_hook. No
        # dictionary record is coalesced, including duplicate Gamma occurrences.
        return value
    if syntax_array(value):
        shared,_=tree(value)
        return shared
    # Root arrays of syntax (registry/Gamma/ports) preserve their original length
    # and order. Pure scalar metadata/factor arrays have no syntax to share.
    for index,child in enumerate(value):
        if type(child) is list:
            value[index]=share_syntax_value(child,memo,identities)
    return value

def reject_nonfinite(token):
    raise ValueError('nonfinite JSON numeric token: ' + token)


def finite_float(token):
    # Authentic scalar cost metadata is a float. It is not an index/port/AST
    # licence; preserving its type and signed zero changes no canonical value.
    value = float(token)
    need(math.isfinite(value), 'nonfinite/overflowing JSON float prohibited')
    return value


def decode_lossless_preparation(raw, budget):
    """Authenticate/decode one complete immutable buffer without file access.

    The caller must relinquish its raw reference after this return and BEFORE
    parsing. Python cannot release an argument still retained by its caller.
    Producer-side budget.check is guidance/accounting, never proof authority.
    """
    budget.check()
    need(type(raw) is bytes and len(raw) == PREPARATION_BYTES,
         'one complete original immutable preparation buffer; no prefix')
    need(hashlib.sha256(raw).hexdigest() == PREPARATION_SHA256,
         'same full original raw preparation SHA')
    budget.check()
    text = raw.decode(json.detect_encoding(raw), 'surrogatepass')
    budget.check()
    return text


def parse_lossless_preparation_text(text, budget):
    """One full stdlib parse, duplicate rejection and value-equal syntax sharing.

    This does not authenticate a filename or authorize altered text. The fixed
    trusted caller passes exactly the text returned by decode above. Holding
    that text through this call is required; it is released after full return.
    Every cache is parse-local and cleared even if budget/syntax work fails.
    """
    budget.check()
    need(type(text) is str, 'exact previously authenticated lossless text')
    memo, identities, objects = {}, {}, [0]
    def unique(pairs):
        objects[0] += 1
        if objects[0] % 128 == 0:
            budget.check()
        result = {}
        for name, value in pairs:
            need(name not in result, 'duplicate JSON field')
            result[name] = share_syntax_value(value, memo, identities)
        return result
    try:
        # Exactly one whole document. json.loads rejects any non-whitespace
        # suffix/second document. No record/row/recipe/occurrence is truncated.
        result = json.loads(text, object_pairs_hook=unique,
                            parse_float=finite_float, parse_constant=reject_nonfinite)
        budget.check()
        return result
    finally:
        memo.clear()
        identities.clear()

