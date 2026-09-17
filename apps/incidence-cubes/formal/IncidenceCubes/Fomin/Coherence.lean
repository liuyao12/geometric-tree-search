import Mathlib

/-! Coordinate coherence. Cross products must separately be nonzero to denote
projective points and lines. Non-incidence requires all four pairings nonzero. -/
namespace IncidenceCubes.Fomin
variable {K : Type*} [Field K]
def dot3 (u v : Fin 3 → K) := u 0 * v 0 + u 1 * v 1 + u 2 * v 2
def cross3 (u v : Fin 3 → K) : Fin 3 → K :=
  ![u 1 * v 2 - u 2 * v 1, u 2 * v 0 - u 0 * v 2, u 0 * v 1 - u 1 * v 0]
def mixedRatio (A B l m : Fin 3 → K) :=
  (dot3 l A * dot3 m B) / (dot3 m A * dot3 l B)
theorem cross_dot_identity (A B l m : Fin 3 → K) :
    dot3 (cross3 A B) (cross3 l m) = dot3 l A * dot3 m B - dot3 m A * dot3 l B := by
  simp [dot3, cross3]; ring
theorem ratio_one_iff_incident (A B l m : Fin 3 → K)
    (hmA : dot3 m A ≠ 0) (hlB : dot3 l B ≠ 0) :
    mixedRatio A B l m = 1 ↔ dot3 (cross3 A B) (cross3 l m) = 0 := by
  rw [cross_dot_identity, sub_eq_zero]
  exact div_eq_one_iff_eq (mul_ne_zero hmA hlB)
end IncidenceCubes.Fomin
