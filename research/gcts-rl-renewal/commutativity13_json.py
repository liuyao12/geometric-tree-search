"""Exact tree-aware JSON streaming using C encoding for each full node.

No field, census, event, candidate or child is omitted. Avoids one Python JSON
generator call and gzip write for every scalar in the large nested trace.
"""
import gzip
import json


def encoded(value):
    return json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()


def dump_tree(value, sink):
    core = {k: v for k, v in value.items() if k != 'children'}
    sink.write(encoded(core)[:-1] + b',"children":[')
    for index, child in enumerate(value['children']):
        if index:
            sink.write(b',')
        head = {k: v for k, v in child.items() if k != 'tree'}
        sink.write(encoded(head)[:-1] + b',"tree":')
        dump_tree(child['tree'], sink)
        sink.write(b'}')
    sink.write(b']}')


def save(path, value):
    with gzip.open(path, 'wb') as sink:
        if 'search' not in value:
            sink.write(encoded(value))
            return
        outer = {k: v for k, v in value.items() if k != 'search'}
        sink.write(encoded(outer)[:-1] + b',"search":')
        search = value['search']
        head = {k: v for k, v in search.items() if k != 'tree'}
        sink.write(encoded(head)[:-1] + b',"tree":')
        dump_tree(search['tree'], sink)
        sink.write(b'}}')
