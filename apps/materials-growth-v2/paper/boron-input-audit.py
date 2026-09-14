"""Download the six 2016 supplementary CIFs and independently audit expansion.

This is an input-admission test, not a claim of learned growth. Output is generated
research data; source CIFs stay in the user-selected output directory.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import subprocess
import io
import re

import ase.io
import gemmi
import numpy as np

FILES = {
    'alpha-B-symmetry.cif': (12, '93bff5cf96e1a8caf43be803b818460c'),
    'beta-B105-symmetry.cif': (105, 'e04123df9e20d6262d00155d5a7afe9f'),
    'beta-B106.cif': (106, 'c9296b8cec730663c1bde8c7b4026e65'),
    'gamma-B-symmetry.cif': (28, 'e28a1a4afdaf1491b7c7acd06998f01f'),
    'tau-B105-symmetry.cif': (210, 'd4eee0a2c71a62cc1087a0c12b79ded7'),
    'tau-B106.cif': (212, '32cb4f39ba11d4c4f339fe19e9bc336c'),
}
BASE = 'https://authors.library.caltech.edu/records/dcaev-djw82/files/'


def audit(path, count, digest):
    raw = path.read_bytes()
    assert hashlib.md5(raw).hexdigest() == digest, 'Repository checksum differs'
    block = gemmi.cif.read_file(str(path)).sole_block()
    assert all(float(x) == 1 for x in block.find_values('_atom_site_occupancy'))
    assert set(block.find_values('_atom_site_type_symbol')) == {'B'}
    fractional = np.array([[float(x) for x in block.find_values('_atom_site_fract_' + axis)]
                           for axis in 'xyz']).T
    ops = [gemmi.Op(x.strip("'\"")) for x in block.find_values('_symmetry_equiv_pos_as_xyz')]
    assert ops, 'No explicit symmetry operations'
    points = []
    for p in fractional:
        for op in ops:
            q = np.mod(op.apply_to_xyz(p.tolist()), 1)
            if not any(np.max(np.abs((q-r+.5) % 1-.5)) < 1e-6 for r in points):
                points.append(q)
    parser_adjustment = None
    if block.find_value('_symmetry_Int_Tables_number') == '0':
        # ASE requires a nominal group even when every operation is explicit.
        # P1 is ONLY an importer placeholder; sitesym overrides its operations.
        text = re.sub(r'(_symmetry_Int_Tables_number\s+)0', r'\g<1>1', raw.decode())
        text = re.sub(r"_symmetry_space_group_name_H-M[^\r\n]*", "_symmetry_space_group_name_H-M 'P 1'", text)
        atoms = ase.io.read(io.BytesIO(text.encode()), format='cif')
        parser_adjustment = 'ASE nominal group placeholder 1; original explicit operations unchanged'
    else:
        atoms = ase.io.read(path)
    assert len(points) == len(atoms) == count, (len(points), len(atoms), count)
    af = atoms.get_scaled_positions()
    assert all(any(np.max(np.abs((q-r+.5) % 1-.5)) < 1e-6 for r in af) for q in points)
    assert atoms.cell.volume > 0 and set(atoms.numbers) == {5}
    distances = atoms.get_all_distances(mic=True)
    np.fill_diagonal(distances, np.inf)
    assert distances.min() > 0.5, 'Coincident or implausibly close sites: inspect input'
    # Independently check the minimum distance by enumerating nearby images.
    cell = atoms.cell.array
    best = float('inf')
    for shift in itertools.product(range(-2, 3), repeat=3):
        delta = (af[:, None, :] - af[None, :, :] + shift) @ cell
        norms = np.linalg.norm(delta, axis=2)
        if shift == (0, 0, 0):
            np.fill_diagonal(norms, np.inf)
        best = min(best, float(norms.min()))
    assert abs(best - distances.min()) < 1e-8
    return {'file': path.name, 'source': BASE + path.name,
            'sha256': hashlib.sha256(raw).hexdigest(), 'atoms': count,
            'asymmetricSites': len(fractional), 'explicitOperations': len(ops),
            'fullOccupancy': True, 'independentExpansionAgrees': True,
            'parserAdjustment': parser_adjustment,
            'minimumDistanceAngstrom': best, 'cell': cell.tolist(),
            'positions': atoms.positions.tolist(),
            'status': 'input-validated; learning and growth not yet tested'}


if __name__ == '__main__':
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for name, (count, digest) in FILES.items():
        path = out / name
        if not path.exists():
            subprocess.run(['curl', '-fsSL', '--max-time', '40',
                BASE + name + '?download=1&fresh=20260914b', '-o', str(path)], check=True)
        result = audit(path, count, digest)
        results.append(result)
        print(json.dumps({k: v for k, v in result.items() if k not in ('positions', 'cell')}), flush=True)
    (out / 'input-audit.json').write_text(json.dumps({'scope': 'six supplementary models; not all boron polymorphs',
        'source': 'https://authors.library.caltech.edu/records/dcaev-djw82', 'results': results}, indent=2))
