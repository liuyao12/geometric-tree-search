"""Post-search connected-existence diagnostics, never input to the search policy."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1])
here = Path(__file__).resolve().parent
# Refuse to start the diagnostic before both prespecified policies have finished.
for phase in ('Ih', 'II', 'VI'):
    for policy in ('baseline', 'support-rich'):
        check = json.loads((root / phase / f'{policy}-check.json').read_text())
        assert len(check['results']) == 2
for phase in ('Ih', 'II', 'VI'):
    folder = root / phase
    source, filtered = folder / 'source.json', folder / 'filtered.json'
    target = folder / 'connected-oracle'
    subprocess.run([sys.executable, str(here / 'ice-factorized-existence-oracle.py'),
                    str(source), str(filtered), str(folder / 'index.json'),
                    str(folder / 'index-check.json'), str(target), '--connected'], check=True)
    subprocess.run([sys.executable, str(here / 'verify-ice-factorized-search.py'),
                    str(source), str(filtered), str(target), str(folder / 'connected-oracle-check.json')], check=True)
    print(json.dumps({'checkedOraclePhase': phase}), flush=True)
