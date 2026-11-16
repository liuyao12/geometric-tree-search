"""Clause tiles with translated, outward literal and term marks."""

from dataclasses import dataclass

from kernel import is_variable, occurs, substitute
from prime_logic import FocusedSearch


@dataclass(frozen=True)
class Port:
    """Signed literal painted on an oriented tile face."""

    sign: bool
    predicate: str
    arity: int

    @classmethod
    def read(cls, literal):
        sign, predicate, arguments = literal
        return cls(sign, predicate, len(arguments))

    def faces(self, other, *, factor=False):
        return ((self.predicate, self.arity) == (other.predicate, other.arity)
                and (self.sign == other.sign) == factor)


def register(arguments, column=0, depth=0):
    """Translate a tile's outward sockets into the common point register."""
    if len(arguments) >= 16:
        raise ValueError('arity exceeds the outward mark radix')
    return {(16*column+i, depth+1): term for i, term in enumerate(arguments, 1)}


def footprint(arguments):
    """The complete outward marks of a literal, including nested sockets."""
    def walk(entries):
        for (column, depth), term in entries.items():
            yield [column, depth, term[0] if isinstance(term, tuple) else term]
            if isinstance(term, tuple):
                yield from walk(register(term[1:], column, depth))

    return list(walk(register(arguments)))


def overlap(left, right, counts, check_time, *, observe=None):
    """Identify corresponding marks and propagate constrained variable fills."""
    a, b = register(left), register(right)
    if a.keys() != b.keys():
        return None
    bindings = {}
    while a:
        check_time()
        address, s = a.popitem()
        t = b.pop(address)
        x, y = substitute(s, bindings), substitute(t, bindings)
        counts['marked_point_joins'] += 1
        counts['solved_equations'] += 1
        if x == y:
            if observe is not None:
                observe(address, x, y, 'match')
            continue
        mirrored = not is_variable(x) and is_variable(y)
        if mirrored:
            x, y = y, x
        if is_variable(x):
            if occurs(x, y):
                if observe is not None:
                    observe(address, y if mirrored else x, x if mirrored else y, 'occurs')
                return None
            if observe is not None:
                observe(address, y if mirrored else x, x if mirrored else y, 'fill')
            fill = {x: y}
            bindings = {v: substitute(t, fill) for v, t in bindings.items()}
            bindings[x] = y
        elif isinstance(x, tuple) and isinstance(y, tuple) and (x[0], len(x)) == (y[0], len(y)):
            if observe is not None:
                observe(address, x, y, 'extend')
            u, v = address
            a.update(register(x[1:], u, v))
            b.update(register(y[1:], u, v))
        else:
            counts['marked_point_conflicts'] += 1
            if observe is not None:
                observe(address, x, y, 'clash')
            return None
    return bindings


class OutwardSearch(FocusedSearch):
    """Use the existing scheduler, with admissibility from the tile marks."""

    unify_arguments = staticmethod(overlap)

    def offer(self, left, first, right, second, *, factor=False):
        a = self.nodes[left]['clause'][first]
        b = self.nodes[right]['clause'][second]
        # The ordinary index already proposes exactly these face pairs. Keep
        # this check here so that an arbitrary proposal cannot bypass the rule.
        if (a[1], len(a[2])) != (b[1], len(b[2])) or (a[0] == b[0]) != factor:
            return None
        return super().offer(left, first, right, second, factor=factor)
