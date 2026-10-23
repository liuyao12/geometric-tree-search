"""Exact obstruction to putting the existing material marks on a planar lattice."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--patch', type=Path, default=HERE/'patch.json')
parser.add_argument('--marks', type=Path, default=HERE/'fixed-marks.json')
parser.add_argument('--output', type=Path, default=HERE/'white-lattice-validation.json')
args = parser.parse_args()
patch_bytes, marks_bytes = args.patch.read_bytes(), args.marks.read_bytes()
patch, marks = json.loads(patch_bytes), json.loads(marks_bytes)

class K:
    """Rational part plus a rational multiple of the square root of five."""
    def __init__(self, a=0, b=0): self.a, self.b = F(a), F(b)
    def __add__(self, other):
        other = field(other)
        return K(self.a+other.a, self.b+other.b)
    __radd__ = __add__
    def __neg__(self): return K(-self.a, -self.b)
    def __sub__(self, other): return self+-field(other)
    def __rsub__(self, other): return field(other)+-self
    def __mul__(self, other):
        other = field(other)
        return K(self.a*other.a+5*self.b*other.b, self.a*other.b+self.b*other.a)
    __rmul__ = __mul__
    def __truediv__(self, other):
        other = field(other)
        denominator = other.a**2-5*other.b**2
        return self*K(other.a/denominator, -other.b/denominator)
    def approximate(self): return float(self.a)+math.sqrt(5)*float(self.b)
def field(value): return value if isinstance(value, K) else K(value)
def defect(point):
    p,q,r,s = point
    return 4*r-2*p-q-K(0,1)*q, 4*r+8*s-3*q+K(0,1)*(2*p+q)
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def cross(a,b): return a[0]*b[1]-a[1]*b[0]

tiles = [3,7,11,28,36]
anchors = {a['tile']:a for a in marks['anchors']}
vectors = []
for tile in tiles:
    anchor = anchors[tile]
    vertices = [patch['vertices'][patch['tiles'][tile][j]] for j in anchor['triangle']]
    a,b,c = [defect(point) for point in vertices]
    denominator = cross(sub(b,a),sub(c,a))
    wb = cross(sub((K(4),K(14)),a),sub(c,a))/denominator
    wc = cross(sub(b,a),sub((K(4),K(14)),a))/denominator
    weights = [1-wb-wc,wb,wc]
    point = [sum(w*v[k] for w,v in zip(weights,vertices)) for k in range(4)]
    assert all(abs(x.approximate()-y)<1e-10 for x,y in zip(point,anchor['coordinates']))
    vectors.append([point[0].a,point[0].b,point[1].a,point[1].b])
rows = [[x-y for x,y in zip(v,vectors[0])] for v in vectors[1:]]
matrix = [row[:] for row in rows]
determinant = F(1)
for col in range(4):
    pivot = next((i for i in range(col,4) if matrix[i][col]),None)
    assert pivot is not None
    if pivot != col:
        matrix[col],matrix[pivot] = matrix[pivot],matrix[col]
        determinant = -determinant
    divisor = matrix[col][col]
    determinant *= divisor
    for i in range(col+1,4):
        multiplier = matrix[i][col]/divisor
        matrix[i] = [x-multiplier*y for x,y in zip(matrix[i],matrix[col])]
assert determinant
report = {
    'tiles':tiles, 'rationalRank':4, 'determinant':str(determinant),
    'differenceRows':[[str(x) for x in row] for row in rows],
    'basis':'Rational and square-root-of-five parts of the first two lattice coefficients',
    'patchSha256':hashlib.sha256(patch_bytes).hexdigest(),
    'marksSha256':hashlib.sha256(marks_bytes).hexdigest(),
    'conclusion':'These five existing marks do not lie in any rank-two planar lattice. An invertible linear screen transformation cannot change this obstruction.',
    'scope':'Existing material marks only. Does not rule out different choices of marks.'
}
args.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
