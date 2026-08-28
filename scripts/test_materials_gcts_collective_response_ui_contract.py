from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_collective_response_is_an_end_to_end_audited_score_channel():
    required_app_fragments = (
        'from "./coherency-graph-field.mjs?v=20260828-305"',
        'scoreTerm("collective-response"',
        'activeCollectiveResponseWeight() * evaluation.collectiveResponse.score',
        'collectiveGraphResponseRanking',
        'id: "long-range"',
        'controlId: "collectiveResponseSelect"',
        'collectiveResponseSelect.addEventListener("change"',
        'collectiveScreeningSelect.addEventListener("change"',
        'collectiveResponseWeightSelect.addEventListener("change"',
        'exp(-hop/${collectiveScreeningLength})',
        'heldoutTargetUsed: false',
    )
    for fragment in required_app_fragments:
        assert fragment in APP

    for control_id in (
        "collectiveResponseSelect",
        "collectiveScreeningSelect",
        "collectiveResponseWeightSelect",
        "collectiveResponseHint",
    ):
        assert f'id="{control_id}"' in HTML

    assert "Build 303" in README
    assert "screened collective graph response" in README.lower()


if __name__ == "__main__":
    test_collective_response_is_an_end_to_end_audited_score_channel()
    print("collective response UI contract passed")
