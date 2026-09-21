"""Small independent RUP checker. Deletions are safely ignored.

Every accepted addition must follow by reverse unit propagation from the
original formula and earlier verified additions. Unsupported RAT-only steps
are rejected. A final contradiction is mandatory.
"""
from collections import defaultdict

class RUPChecker:
    def __init__(self, clauses):
        self.clauses, self.watches, self.positions, self.units = [], defaultdict(set), [], []
        self.empty = False
        self.maximum = 0
        for c in clauses:
            self.add(c)

    def add(self, clause):
        clause = list(dict.fromkeys(clause))
        self.maximum = max([self.maximum]+[abs(x) for x in clause])
        if not clause:
            self.empty = True
        elif len(clause) == 1:
            self.units.append(clause[0])
        else:
            i = len(self.clauses)
            self.clauses.append(clause)
            self.positions.append([0,1])
            self.watches[clause[0]].add(i)
            self.watches[clause[1]].add(i)

    def implied(self, clause):
        if self.empty:
            return True
        size = max([self.maximum]+[abs(x) for x in clause])+1
        values = [0]*size
        queue = []
        def value(lit):
            return values[abs(lit)]*(1 if lit > 0 else -1)
        def assign(lit):
            old = value(lit)
            if old == -1: return False
            if old == 0:
                values[abs(lit)] = 1 if lit > 0 else -1
                queue.append(lit)
            return True
        for lit in self.units+[-x for x in clause]:
            if not assign(lit): return True
        cursor = 0
        while cursor < len(queue):
            false_lit = -queue[cursor]
            cursor += 1
            for ci in list(self.watches[false_lit]):
                c, positions = self.clauses[ci], self.positions[ci]
                which = 0 if c[positions[0]] == false_lit else 1
                other = positions[1-which]
                if value(c[other]) == 1: continue
                replacement = next((i for i,l in enumerate(c) if i not in positions and value(l) != -1), None)
                if replacement is not None:
                    self.watches[false_lit].remove(ci)
                    positions[which] = replacement
                    self.watches[c[replacement]].add(ci)
                elif not assign(c[other]):
                    return True
        return False

    def verify(self, proof):
        checked = 0
        for line in proof:
            words = line.split()
            if not words or words[0] in ('d','c'): continue
            numbers = list(map(int,words))
            if not numbers or numbers[-1] != 0: raise ValueError('Unterminated proof clause')
            clause = numbers[:-1]
            if 0 in clause or not self.implied(clause): raise ValueError(f'Non-RUP addition at step {checked+1}')
            self.add(clause)
            checked += 1
        if not self.implied([]): raise ValueError('Proof has no final contradiction')
        return {'verified':True, 'method':'independent reverse unit propagation', 'additions':checked}
