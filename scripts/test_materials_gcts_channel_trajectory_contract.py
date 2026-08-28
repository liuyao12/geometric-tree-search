#!/usr/bin/env python3
"""Static contract for Build 296's actual GCTS coefficient trajectories."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(source: str, needle: str) -> None:
    assert needle in source, f"missing contract text: {needle}"


def test_channel_trajectory_contract() -> None:
    require(APP, "function sectionChannelTrajectoryRecord(prototype)")
    require(APP, "function renderClusterChannelTrajectory(inspector, prototype)")
    require(APP, 'label: `A${axisIndex + 1}`')
    require(APP, '"deterministic intrinsic spherical-code coefficient axes"')
    require(APP, 'capacityBasis: "pose × port pivot columns determine required dimension; they are not asserted to be the fitted coefficient axes"')
    require(APP, 'class="cluster-channel-learning"')
    require(APP, "controls.replaceChildren()")
    require(APP, "Held-out samples never update coefficients")
    require(APP, "channelLearningTrajectory: channelLearning ?")
    require(APP, "targetUsed: false")
    require(APP, "physicalPotential: false")
    require(APP, 'buildId: "20260828-308"')
    require(HTML, 'app.js?v=20260828-308')
    require(HTML, 'style.css?v=20260828-308')
    require(STYLE, ".cluster-channel-learning-chart .channel-coefficient-path")
    require(STYLE, ".cluster-channel-learning-controls button.inactive")
    require(README, "Build 296 · actual channel-learning trajectories")
    require(README, "not presented as an unproved change of basis")


if __name__ == "__main__":
    test_channel_trajectory_contract()
    print("channel trajectory contract passed")
