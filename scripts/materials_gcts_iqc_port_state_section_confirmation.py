#!/usr/bin/env python3
"""Confirm a continuous parent/source port-state section on two IQC waves."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from materials_gcts_iqc_self_fed_section_confirmation import (
    CONFIRMATION_CENTER as PRIOR_CONFIRMATION_CENTER, evaluate as evaluate_stage)


CONFIRMATION_CENTER = (0., -50., 0.)


def evaluate():
    return evaluate_stage(
        confirmation_center=CONFIRMATION_CENTER,
        descriptor_version="port-state-v2",
        prior_confirmation_centers=(PRIOR_CONFIRMATION_CENTER,))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
