"""Read-only copied JSON decoder; no audit/producer code imported.

The delimiter loops accept a trailing comma. This is not a generic strict JSON
validator; inputs are exact pinned known standard JSON produced by json.dumps.
Only decoding is reused, not scientific checking or authority.
"""
import json


def require(condition, message):
    if not condition:
        raise ValueError(message)


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON dictionary key")
        result[key] = value
    return result



class StreamingObject:
    """Standard-library decoder with a bounded retained top-level record.

    This does not trust producer framing: every delimiter/key is parsed, all
    duplicate keys are rejected, and the final JSON/file end is checked.
    A whole 'records' array is never simultaneously retained. Other top-level
    fields and one individual record may use at most the predeclared buffer.
    """
    def __init__(self, handle, max_buffer=16777216):
        self.handle = handle
        self.buffer = ""
        self.position = 0
        self.eof = False
        self.limit = max_buffer
        self.decoder = json.JSONDecoder(object_pairs_hook=object_pairs)

    def fill(self):
        require(not self.eof, "unexpected JSON end")
        more = self.handle.read(65536)
        if not more:
            self.eof = True
            return False
        self.buffer += more
        require(len(self.buffer) <= self.limit, "per-record JSON buffer gate exceeded")
        return True

    def whitespace(self):
        while True:
            while self.position < len(self.buffer) and self.buffer[self.position].isspace():
                self.position += 1
            if self.position < len(self.buffer) or self.eof:
                return
            self.fill()

    def peek(self):
        self.whitespace()
        return self.buffer[self.position] if self.position < len(self.buffer) else None

    def token(self, character):
        require(self.peek() == character, "invalid JSON delimiter: expected " + character)
        self.position += 1

    def value(self):
        self.whitespace()
        while True:
            try:
                value, end = self.decoder.raw_decode(self.buffer, self.position)
                self.position = end
                return value
            except json.JSONDecodeError:
                require(not self.eof and self.fill(), "malformed or truncated JSON value")

    def trim(self):
        self.buffer = self.buffer[self.position:]
        self.position = 0

    def entries(self):
        self.token("{")
        seen = set()
        while self.peek() != "}":
            key = self.value()
            require(isinstance(key, str) and key not in seen, "duplicate/invalid top-level key")
            seen.add(key)
            self.token(":")
            if key == "records":
                self.token("[")
                index = 0
                while self.peek() != "]":
                    value = self.value()
                    yield "record", index, value
                    index += 1
                    self.trim()
                    if self.peek() != "]":
                        self.token(",")
                self.token("]")
                yield "record_count", key, index
            else:
                value = self.value()
                yield "field", key, value
            self.trim()
            if self.peek() != "}":
                self.token(",")
        self.token("}")
        require(self.peek() is None and self.eof, "trailing data after JSON object")



def expansion_records(path, fields):
    import gzip
    with gzip.open(path, 'rt') as handle:
        for kind, key, value in StreamingObject(handle).entries():
            if kind == 'field':
                fields[key] = value
            elif kind == 'record':
                yield value
            else:
                require(kind == 'record_count' and key == 'records' and value == 171,
                        'unexpected compact reader record census')
