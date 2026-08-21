#!/usr/bin/env python3

from materials_gcts_iqc_port_obligation_confirmation import OneShotOrderGuard


def test_one_shot_order_guard():
    guard = OneShotOrderGuard()
    for event in ("protocol-verified", "model-frozen", "seed-frozen",
                  "candidates-frozen", "execution-frozen"):
        guard.record(event)
    assert guard.open_target(lambda: "sealed-target") == "sealed-target"
    guard.scored()
    assert guard.events[-2:] == ["target-opened", "scored"]
    try:
        guard.open_target(lambda: None)
    except AssertionError:
        pass
    else:
        raise AssertionError("target factory opened twice")
    try:
        guard.record("execute-again")
    except AssertionError:
        pass
    else:
        raise AssertionError("execution resumed after target open")


def main():
    test_one_shot_order_guard()
    print("IQC port-obligation confirmation harness passed")


if __name__ == "__main__":
    main()
