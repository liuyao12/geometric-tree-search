import IncidenceCubes.Penrose.Algebra

/-! A coordinate bridge, not a reduction of Penrose to Fomin--Pylyavskyy.
The Veronese constraint is retained; coefficient vectors are not zero sets. -/
namespace IncidenceCubes.Connection
variable {K : Type*} [Field K]
abbrev ConicCoefficients (K : Type*) := Fin 6 → K
def evalConic (q : ConicCoefficients K) (x : Fin 3 → K) :=
  q 0 * x 0 ^ 2 + q 1 * x 1 ^ 2 + q 2 * x 2 ^ 2 +
  q 3 * x 0 * x 1 + q 4 * x 0 * x 2 + q 5 * x 1 * x 2
def evalLine (l x : Fin 3 → K) := l 0 * x 0 + l 1 * x 1 + l 2 * x 2
def doubleLine (l : Fin 3 → K) : ConicCoefficients K :=
  ![l 0 ^ 2, l 1 ^ 2, l 2 ^ 2, 2 * l 0 * l 1, 2 * l 0 * l 2, 2 * l 1 * l 2]
theorem eval_doubleLine (l x : Fin 3 → K) :
    evalConic (doubleLine l) x = evalLine l x ^ 2 := by
  simp [evalConic, doubleLine, evalLine]; ring
theorem doubleLine_rescale (s : K) (l : Fin 3 → K) :
    doubleLine (s • l) = s ^ 2 • doubleLine l := by
  funext i
  fin_cases i <;> simp [doubleLine] <;> ring
theorem doubleLine_ne_zero (l : Fin 3 → K) (hl : l ≠ 0) : doubleLine l ≠ 0 := by
  intro h
  apply hl
  funext i
  fin_cases i
  · have hz := congrFun h 0
    simpa [doubleLine, sq_eq_zero_iff] using hz
  · have hz := congrFun h 1
    simpa [doubleLine, sq_eq_zero_iff] using hz
  · have hz := congrFun h 2
    simpa [doubleLine, sq_eq_zero_iff] using hz
def InPencil (q r t : ConicCoefficients K) : Prop := ∃ a b : K, t = a • q + b • r
theorem rank_one_pencil (q : ConicCoefficients K) (l : Fin 3 → K) (a b : K) :
    InPencil q (doubleLine l) (a • q + b • doubleLine l) ∧
    ∀ x, evalConic (a • q + b • doubleLine l) x =
      a * evalConic q x + b * evalLine l x ^ 2 := by
  constructor
  · exact ⟨a, b, rfl⟩
  · intro x; simp [evalConic, doubleLine, evalLine]; ring
end IncidenceCubes.Connection
