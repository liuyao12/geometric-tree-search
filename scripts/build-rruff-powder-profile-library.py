#!/usr/bin/env python3
"""Build the browser-sized, provenance-pinned RRUFF powder profile library.

The scientific source is the JARVIS-normalized RRUFF powder-XRD snapshot on
Figshare.  Wavelength and space-group metadata are independently read from the
official RRUFF DIF archive.  This script intentionally retains the measured,
processed XY ordinates without smoothing or peak picking.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


PROFILE_IDS = (
    "R070292", "R070534", "R070586",  # halite replicates
    "R050503",  # graphite
    "R050145",  # diamond-cubic silicon
    "R040078", "R060195",  # aragonite
    "R050127", "R050128", "R050307",  # calcite
    "R050591",  # brookite
    "R050031", "R050417", "R060493", "R060745",  # rutile
)

FIGSHARE_RECORD = "https://doi.org/10.6084/m9.figshare.31817977.v1"
FIGSHARE_FILE = "https://ndownloader.figshare.com/files/62967574"
FIGSHARE_ZIP_SHA256 = "139e4ea9319fc7d7e31c08b5599a2afef7e6d9ea375f1076a4947b33bff9d59a"
RRUFF_DIF_ARCHIVE = "https://www.rruff.net/zipped_data_files/powder/DIF.zip"
RRUFF_DIF_ZIP_SHA256 = "3b540db61664cacdd22268ffbac6ab586ca6bce389b7399cc3e9baaeb6607b03"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def require_sha256(path: Path, expected: str) -> None:
    actual = sha256_bytes(path.read_bytes())
    if actual != expected:
        raise RuntimeError(f"{path} SHA-256 {actual} != pinned {expected}")


def normalized_formula(formula: str) -> str:
    return re.sub(r"(?<=\D)1\.00|(?<=\D)1(?=\D|$)", "", formula)


def dif_metadata(archive: zipfile.ZipFile, rruff_id: str) -> dict[str, object]:
    names = [name for name in archive.namelist() if rruff_id in name]
    if len(names) != 1:
        raise RuntimeError(f"expected one DIF record for {rruff_id}, found {len(names)}")
    text = archive.read(names[0]).decode("utf-8", errors="replace")
    wavelength = re.search(r"X-RAY WAVELENGTH:\s*([0-9.]+)", text)
    space_group = re.search(r"SPACE GROUP:\s*([^\r\n]+)", text)
    if not wavelength or not space_group:
        raise RuntimeError(f"missing wavelength or space group in {names[0]}")
    return {
        "wavelengthAngstrom": float(wavelength.group(1)),
        "spaceGroup": space_group.group(1).strip(),
        "difArchiveMember": names[0],
        "difTextSha256": sha256_bytes(text.encode("utf-8")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jarvis-zip", required=True, type=Path)
    parser.add_argument("--rruff-dif-zip", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    require_sha256(arguments.jarvis_zip, FIGSHARE_ZIP_SHA256)
    require_sha256(arguments.rruff_dif_zip, RRUFF_DIF_ZIP_SHA256)

    with zipfile.ZipFile(arguments.jarvis_zip) as source_archive:
        [source_name] = source_archive.namelist()
        source_records = json.loads(source_archive.read(source_name))
    by_id = {record["##RRUFFID"]: record for record in source_records}

    records = []
    with zipfile.ZipFile(arguments.rruff_dif_zip) as dif_archive:
        for rruff_id in PROFILE_IDS:
            source = by_id[rruff_id]
            x = [float(value) for value in source["x"]]
            y = [float(value) for value in source["y"]]
            if len(x) != len(y) or len(x) < 12 or any(b <= a for a, b in zip(x, x[1:])):
                raise RuntimeError(f"invalid XY profile for {rruff_id}")
            profile_payload = json.dumps({"x": x, "y": y}, separators=(",", ":")).encode()
            records.append({
                "rruffId": rruff_id,
                "phase": source["##NAMES"],
                "formula": normalized_formula(source["formula"]),
                "elements": sorted(source["elements"]),
                "sampleDescription": source["##DIFFRACTION SAMPLE DESCRIPTION"],
                "status": source["##STATUS"],
                "source": source["##SOURCE"],
                "locality": source["##LOCALITY"],
                "cellParameters": source["##CELL PARAMETERS"],
                "sourceUrl": f"https://www.rruff.net/{rruff_id}",
                "profileSha256": sha256_bytes(profile_payload),
                **dif_metadata(dif_archive, rruff_id),
                "axis": "two-theta-degree",
                "intensityUnits": "RRUFF processed arbitrary intensity",
                "uncertainty": "not supplied; uniform unit weights required",
                "resolution": "not supplied in normalized record",
                "x": x,
                "y": y,
            })

    library = {
        "schema": "gcts-rruff-powder-profile-library-v1",
        "title": "RRUFF experimental powder profiles · JARVIS normalized subset",
        "license": "CC BY 4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
        "datasetDoi": FIGSHARE_RECORD,
        "datasetFileUrl": FIGSHARE_FILE,
        "datasetFileSha256": FIGSHARE_ZIP_SHA256,
        "rruffDifArchiveUrl": RRUFF_DIF_ARCHIVE,
        "rruffDifArchiveSha256": RRUFF_DIF_ZIP_SHA256,
        "selectionRule": "predeclared polymorph and replicate subset; never selected by fit to portal geometry",
        "profileCount": len(records),
        "profiles": records,
    }
    serialized = (json.dumps(library, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(serialized)
    print(f"wrote {len(records)} profiles, {len(serialized)} bytes, sha256={sha256_bytes(serialized)}")


if __name__ == "__main__":
    main()
