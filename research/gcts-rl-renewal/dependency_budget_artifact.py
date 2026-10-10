"""Lazy, SHA-bound access to full original comparison traces."""
import json
from pathlib import Path
from receptor_attention_artifact import Cases


def load(path):
    path=Path(path);data=json.loads(path.read_text())
    data['cases']=Cases(path.parent,data.pop('case_files'),wrapped=False)
    return data
