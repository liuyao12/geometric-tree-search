import Mathlib

/-! Edge-cancellation certificate extracted from an oriented bicolored
quadrangulation. No topological manifold-recognition theorem is asserted. -/
namespace IncidenceCubes.Fomin
open scoped BigOperators
structure ClosedQuadrangulation (Face Edge : Type*) where
  positive : (Face × Fin 2) ≃ Edge
  negative : (Face × Fin 2) ≃ Edge
variable {Face Edge G : Type*} [Fintype Face] [Fintype Edge] [CommGroup G]
def faceWeight (T : ClosedQuadrangulation Face Edge) (w : Edge → G) (f : Face) : G :=
  (∏ i : Fin 2, w (T.positive (f, i))) / (∏ i : Fin 2, w (T.negative (f, i)))
theorem total_product (T : ClosedQuadrangulation Face Edge) (w : Edge → G) :
    (∏ f : Face, faceWeight T w f) = 1 := by
  classical
  unfold faceWeight
  rw [Finset.prod_div_distrib]
  have hp : (∏ f : Face, ∏ i : Fin 2, w (T.positive (f, i))) = ∏ e : Edge, w e := by
    rw [← Fintype.prod_prod_type (fun x : Face × Fin 2 => w (T.positive x))]
    exact Equiv.prod_comp T.positive w
  have hn : (∏ f : Face, ∏ i : Fin 2, w (T.negative (f, i))) = ∏ e : Edge, w e := by
    rw [← Fintype.prod_prod_type (fun x : Face × Fin 2 => w (T.negative x))]
    exact Equiv.prod_comp T.negative w
  rw [hp, hn]
  exact div_self' _
theorem last_face (T : ClosedQuadrangulation Face Edge) (w : Edge → G) (missing : Face)
    (h : ∀ f, f ≠ missing → faceWeight T w f = 1) : faceWeight T w missing = 1 := by
  classical
  have hs : (∏ f : Face, faceWeight T w f) = faceWeight T w missing := by
    apply Finset.prod_eq_single missing
    · intro f _ hf; exact h f hf
    · intro hm; exact False.elim (hm (Finset.mem_univ missing))
  exact hs.symm.trans (total_product T w)
def positiveIndex : Fin 12 → Fin 12 := ![0,5,11,8,2,4,7,6,1,9,10,3]
def negativeIndex : Fin 12 → Fin 12 := ![3,1,10,9,8,0,11,5,6,2,7,4]
def slotIndex (x : Fin 6 × Fin 2) : Fin 12 := ⟨2 * x.1.val + x.2.val, by omega⟩
private theorem slot_bijective : Function.Bijective slotIndex := by decide
private theorem positive_bijective : Function.Bijective positiveIndex := by decide
private theorem negative_bijective : Function.Bijective negativeIndex := by decide
noncomputable def cube : ClosedQuadrangulation (Fin 6) (Fin 12) where
  positive := (Equiv.ofBijective slotIndex slot_bijective).trans
    (Equiv.ofBijective positiveIndex positive_bijective)
  negative := (Equiv.ofBijective slotIndex slot_bijective).trans
    (Equiv.ofBijective negativeIndex negative_bijective)
theorem cube_last_face (w : Fin 12 → G) (missing : Fin 6)
    (h : ∀ f, f ≠ missing → faceWeight cube w f = 1) : faceWeight cube w missing = 1 :=
  last_face cube w missing h
end IncidenceCubes.Fomin
