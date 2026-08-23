"""Contract for the geometry-only fresh parent-balanced preregistration."""

from materials_gcts_iqc_parent_balanced_confirmation_preregistration import (
    CONFIRMATION_CENTER, MINIMUM_REQUIRED_DOMAIN_SEPARATION, PRIOR_CENTERS,
    OneShotOrderGuard, select_confirmation_center, validate_preregistration)


def test_parent_balanced_center_is_reproducible_and_fresh():
    assert select_confirmation_center() == CONFIRMATION_CENTER == \
        (280., 220., 0.)
    assert CONFIRMATION_CENTER not in PRIOR_CENTERS
    assert validate_preregistration()
    import math
    assert min(math.dist(CONFIRMATION_CENTER, prior)
               for prior in PRIOR_CENTERS) > \
        MINIMUM_REQUIRED_DOMAIN_SEPARATION


def test_one_shot_order_guard_fails_closed():
    guard = OneShotOrderGuard()
    try:
        guard.seed_opened()
        raise AssertionError("seed opened before protocol")
    except RuntimeError:
        pass
    guard.protocol_verified()
    guard.seed_opened()
    digest = "a" * 64
    guard.receipt_frozen(digest)
    guard.target_opened()
    guard.scored(digest)
    assert guard.audit() == {
        "state": "scored", "seed_open_count": 1,
        "target_open_count": 1, "score_count": 1,
        "receipt_digest": digest}
    for action in (guard.target_opened,
                   lambda: guard.scored(digest)):
        try:
            action()
            raise AssertionError("one-shot action repeated")
        except RuntimeError:
            pass


if __name__ == "__main__":
    test_parent_balanced_center_is_reproducible_and_fresh()
    test_one_shot_order_guard_fails_closed()
    print("parent-balanced confirmation preregistration: passed")
