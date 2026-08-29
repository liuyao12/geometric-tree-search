from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
NORMALIZATION = (ROOT / "apps/iqc-growth-live/score-normalization.mjs").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_constraint_tensor_is_an_end_to_end_physics_channel():
    fragments = (
        'from "./geometric-constraint-tensor.mjs?v=20260828-316"',
        'scoreTerm("constraint-tensor"',
        'activeConstraintTensorWeight() * evaluation.constraintTensor.score',
        'geometricConstraintTensorRanking',
        'id: "constraint-rigidity"',
        'controlId: "constraintTensorSelect"',
        'constraintTensorSelect.addEventListener("change"',
        'forceConstantsUsed: false',
        'phononSpectrumInferred: false',
    )
    for fragment in fragments:
        assert fragment in APP
    for control in ("constraintTensorSelect", "constraintTensorWeightSelect", "constraintTensorHint"):
        assert f'id="{control}"' in HTML
    assert '"constraint-tensor": "constraint-rigidity"' in NORMALIZATION
    assert "Build 305" in README


if __name__ == "__main__":
    test_constraint_tensor_is_an_end_to_end_physics_channel()
    print("constraint tensor UI contract passed")
