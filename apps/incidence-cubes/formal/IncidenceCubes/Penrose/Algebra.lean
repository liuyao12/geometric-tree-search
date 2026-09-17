import Mathlib

/-! Polynomial kernel of Penrose's conic cube. These identities construct
normalized cubes. The normal-form theorem for arbitrary geometric input and
ordinary tangency/nondegeneracy are separate, as yet unimplemented theorems. -/
namespace IncidenceCubes.Penrose
variable {R : Type*} [CommRing R]
def D2 (d e a : R) := d * e - a ^ 2
def D3 (d e f a b c : R) :=
  d * e * f + 2 * a * b * c - d * c ^ 2 - e * b ^ 2 - f * a ^ 2
def F1 (q p d : R) := d * q - p ^ 2
def F2 (q p r d e a : R) :=
  D2 d e a * q - e * p ^ 2 + 2 * a * p * r - d * r ^ 2
def F3 (q p r s d e f a b c : R) :=
  D3 d e f a b c * q - (e * f - c ^ 2) * p ^ 2
    - (d * f - b ^ 2) * r ^ 2 - (d * e - a ^ 2) * s ^ 2
    - 2 * (b * c - a * f) * p * r - 2 * (a * c - e * b) * p * s
    - 2 * (a * b - d * c) * r * s
def L1 (p r d a : R) := d * r - a * p
def L2 (p r s d e a b c : R) :=
  D2 d e a * s - (e * b - a * c) * p - (d * c - a * b) * r

theorem bottom_edge (q p d : R) : d * q - F1 q p d = p ^ 2 := by
  dsimp [F1]; ring

theorem middle_edge (q p r d e a : R) :
    D2 d e a * F1 q p d - d * F2 q p r d e a = (L1 p r d a) ^ 2 := by
  dsimp [D2, F1, F2, L1]; ring

theorem top_edge (q p r s d e f a b c : R) :
    D3 d e f a b c * F2 q p r d e a - D2 d e a * F3 q p r s d e f a b c =
      (L2 p r s d e a b c) ^ 2 := by
  dsimp [D2, D3, F2, F3, L2]; ring

theorem exists_algebraic_eighth (q p r s d e f a b c : R) :
    ∃ t : R,
      D3 d e f a b c * F2 q p r d e a - D2 d e a * t = (L2 p r s d e a b c) ^ 2 ∧
      D3 d e f a b c * F2 q p s d f b - D2 d f b * t = (L2 p s r d f b a c) ^ 2 ∧
      D3 d e f a b c * F2 q r s e f c - D2 e f c * t = (L2 r s p e f c a b) ^ 2 := by
  refine ⟨F3 q p r s d e f a b c, ?_, ?_, ?_⟩
  · exact top_edge q p r s d e f a b c
  · dsimp [D2, D3, F2, F3, L2]; ring
  · dsimp [D2, D3, F2, F3, L2]; ring

theorem face_pencil_identity (p r s d e a b c : R) :
    D2 d e a * L1 p s d b - (d * c - a * b) * L1 p r d a =
      d * L2 p r s d e a b c := by
  dsimp [D2, L1, L2]; ring

theorem top_face_common_zero {K : Type*} [Field K] (p r s d e a b c : K)
    (hd : d ≠ 0) (hu : L1 p r d a = 0) (hv : L1 p s d b = 0) :
    L2 p r s d e a b c = 0 := by
  have h := face_pencil_identity p r s d e a b c
  rw [hu, hv] at h
  have hz : d * L2 p r s d e a b c = 0 := by simpa using h.symm
  exact (mul_eq_zero.mp hz).resolve_left hd

def polar {V : Type*} [Add V] (q : V → R) (x y : V) := q (x + y) - q x - q y

theorem polar_rank_one_update {V : Type*} [Add V] (q p : V → R) (a b : R) (x y : V)
    (hp : p (x + y) = p x + p y) :
    polar (fun z => a * q z + b * (p z) ^ 2) x y =
      a * polar q x y + 2 * b * p x * p y := by
  dsimp [polar]; rw [hp]; ring

theorem polar_agrees_on_chord {V : Type*} [Add V] (q p : V → R) (a b : R) (x y : V)
    (hp : p (x + y) = p x + p y) (hx : p x = 0) :
    polar (fun z => a * q z + b * (p z) ^ 2) x y = a * polar q x y := by
  rw [polar_rank_one_update q p a b x y hp, hx]; ring
end IncidenceCubes.Penrose
