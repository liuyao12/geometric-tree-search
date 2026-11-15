"""Replay equality-free CNF certificates without calling the search kernel."""


class InvalidProof(ValueError):
    """The supplied records do not prove a refutation of the supplied input."""


def require(condition, message):
    if not condition:
        raise InvalidProof(message)


def variable(word):
    return isinstance(word, str) and word.startswith("?") and len(word) > 1


class Signature:
    """Keep term and literal alphabets fixed while checking the certificate."""

    def __init__(self):
        self.predicates = {}
        self.functions = {}

    @staticmethod
    def arity(registry, symbol, count, add):
        if add:
            registry.setdefault(symbol, count)
        require(registry.get(symbol) == count, f"unknown symbol or arity mismatch: {symbol!r}")

    def term(self, raw, add=False):
        if isinstance(raw, str):
            require(bool(raw) and raw != "?", "invalid atom or variable")
            if not variable(raw):
                self.arity(self.functions, raw, 0, add)
            return raw
        require(isinstance(raw, (tuple, list)) and len(raw) >= 2, "invalid compound term")
        function = raw[0]
        require(isinstance(function, str) and bool(function)
                and not function.startswith("?"), "invalid function name")
        self.arity(self.functions, function, len(raw)-1, add)
        return (function, *(self.term(child, add) for child in raw[1:]))

    def clause(self, raw, add=False):
        require(isinstance(raw, (tuple, list)), "expected a clause")
        result = []
        for item in raw:
            require(isinstance(item, (tuple, list)) and len(item) == 3, "invalid literal")
            sign, predicate, args = item
            require(type(sign) is bool and isinstance(predicate, str) and bool(predicate)
                    and not predicate.startswith("?") and predicate not in {"=", "!=", "$equal", "$distinct"}
                    and isinstance(args, (tuple, list)), "invalid signed equality-free atom")
            self.arity(self.predicates, predicate, len(args), add)
            result.append((sign, predicate, tuple(self.term(child, add) for child in args)))
        return tuple(result)


def free_terms(terms):
    names = set()
    pending = list(terms)
    while pending:
        t = pending.pop()
        if variable(t):
            names.add(t)
        elif isinstance(t, tuple):
            pending.extend(t[1:])
    return names


def free_clause(clause):
    return free_terms(term for literal in clause for term in literal[2])


def instantiation(clause, environment):
    def instance(term):
        if isinstance(term, str):
            return environment.get(term, term)
        function, *arguments = term
        return (function, *(instance(t) for t in arguments))

    return tuple((sign, predicate, tuple(instance(t) for t in args)) for sign, predicate, args in clause)


def standardized(clause, prefix):
    names = sorted(free_clause(clause))
    return instantiation(clause, dict(zip(names, (f"?{prefix}{i}" for i in range(len(names))))))


def renaming(clause, raw):
    require(isinstance(raw, dict) and raw.keys() == free_clause(clause),
            "renaming must cover precisely the result variables")
    require(all(variable(x) for x in raw.values()) and len(set(raw.values())) == len(raw),
            "renaming must be injective and introduce only variable names")
    return instantiation(clause, raw)


def position(value, extent):
    return type(value) is int and 0 <= value < extent


def derive(line, prior, signature):
    rule = line["rule"]
    require(set(line) == {"rule", "parents", "sites", "substitution", "renaming", "clause"},
            "inference provenance fields do not match the certificate format")
    parents = line["parents"]
    expected_parents = 1 if rule == "factor" else 2
    require(isinstance(parents, (list, tuple)) and len(parents) == expected_parents
            and all(position(i, len(prior)) for i in parents), "invalid proof parents")
    left = standardized(prior[parents[0]], "L")
    right = left if rule == "factor" else standardized(prior[parents[1]], "R")
    sites = line["sites"]
    require(isinstance(sites, (list, tuple)) and len(sites) == 2
            and position(sites[0], len(left)) and position(sites[1], len(right)),
            "invalid literal positions")
    i, j = sites
    unifier = line["substitution"]
    scope = free_clause(left) | free_clause(right)
    require(isinstance(unifier, dict) and unifier.keys() <= scope, "substitution escapes its parent scopes")
    bindings = {name: signature.term(term) for name, term in unifier.items()}
    require(free_terms(bindings.values()) <= scope-bindings.keys(),
            "substitution is cyclic, unnormalized or contains a foreign variable")
    left = instantiation(left, bindings)
    right = left if rule == "factor" else instantiation(right, bindings)
    if rule == "factor":
        require(i != j and left[i] == left[j], "factoring requires distinct same-sign unified literals")
        return left[:j]+left[j+1:]
    sign, predicate, args = left[i]
    require(right[j] == (not sign, predicate, args), "resolution requires complementary unified literals")
    return left[:i]+left[i+1:]+right[:j]+right[j+1:]


def verify(clauses, proof):
    """Check input provenance, scopes, substitutions and a final empty clause.

    Substitutions are replayed as explicit simultaneous maps. They need not
    be most general, but their variables must belong to the standardized
    parents and the maps must be idempotent. Factoring uses a single scope.
    """
    registry = Signature()
    require(isinstance(clauses, (list, tuple)), "expected source clauses in order")
    source = tuple(registry.clause(row, add=True) for row in clauses)
    require(isinstance(proof, dict) and set(proof) == {"format", "steps", "root"}
            and proof["format"] == "lifted-cnf-v1", "unrecognized certificate")
    steps = proof["steps"]
    require(isinstance(steps, (list, tuple)) and bool(steps) and position(proof["root"], len(steps))
            and proof["root"] == len(steps)-1, "invalid proof root")
    verified = []
    for line in steps:
        require(isinstance(line, dict) and line.get("rule") in ("input", "resolve", "factor")
                and "clause" in line and "renaming" in line, "unsupported proof record")
        row = registry.clause(line["clause"])
        require(len(set(row)) == len(row), "recorded clauses must have distinct literals")
        if line["rule"] == "input":
            require(set(line) == {"rule", "source", "renaming", "clause"}
                    and position(line["source"], len(source)), "invalid input provenance")
            expected = source[line["source"]]
        else:
            expected = derive(line, verified, registry)
        require(set(row) == set(renaming(expected, line["renaming"])),
                "clause differs from the cited inference result")
        verified.append(row)
    require(not verified[proof["root"]], "proof root is not the empty clause")
    return True
