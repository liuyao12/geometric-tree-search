"""Read only grid/identity columns; export the <=12-crossing lattice benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import xlrd

parser = argparse.ArgumentParser()
parser.add_argument('workbook')
parser.add_argument('output')
args = parser.parse_args()
sheet = xlrd.open_workbook(args.workbook, on_demand=True).sheet_by_index(0)
headers = sheet.row_values(0)
columns = {k: headers.index(k) for k in ['name', 'crossing_number', 'grid_notation']}
records = []
for row in range(2, sheet.nrows):
    name, crossing, grid = [sheet.cell_value(row, columns[k]) for k in columns]
    try:
        crossing = int(crossing)
    except (ValueError, TypeError):
        continue
    if not 0 <= crossing <= 12:
        continue
    if not grid and crossing:
        raise ValueError(f'Missing grid: {name}')
    records.append({'id': name, 'crossings': crossing,
                    'grid': json.loads(grid) if grid else None,
                    'sourceRow': row + 1})
assert len(records) == 2978 and len({r['id'] for r in records}) == len(records)
output = {'version': 'knotinfo-grid-input-v1', 'source': {
    'url': 'https://raw.githubusercontent.com/knotinfo-org/assets/main/knotinfo_data_complete.xls.zip',
    'documentation': 'https://linkinfo.knotinfo.org/descriptions/grid_notation.html',
    'workbookSha256': hashlib.sha256(Path(args.workbook).read_bytes()).hexdigest(),
    'sheet': sheet.name, 'columnsRead': columns,
    'labelRole': 'reference/evaluation metadata only; never search features'},
    'scope': 'Unknot and prime reference types through 12 crossings; composite coverage deferred; mirrors generated separately.',
    'records': records}
Path(args.output).write_text(json.dumps(output, separators=(',', ':')) + '\n')
print(json.dumps({'records': len(records), 'output': args.output}))
