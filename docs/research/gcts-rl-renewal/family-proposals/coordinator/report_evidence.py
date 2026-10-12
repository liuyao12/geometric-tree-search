"""Exact file projection and historical public-route reuse; no research execution."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = Path('/private/tmp/gcts-family-router-publish-20261010')
PREFIX = 'docs/research/gcts-rl-renewal/family-proposals/'
DEST = ROOT / PREFIX


def pin(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return {'sha256': h.hexdigest(), 'bytes': Path(path).stat().st_size}


def load(path):
    return json.loads(Path(path).read_text())


def project(folders, historical_sources=None):
    """Call only after scientific owners are terminal and sources frozen."""
    DEST.mkdir(exist_ok=True)
    files, origins, requirements = set(), [], {}
    external_runtime = {}
    historical_sources = historical_sources or {}
    overrides = {}

    def require(path, expected_sha, expected_bytes=None):
        source = Path(path)
        source = source if source.is_absolute() else ROOT / source
        assert source.is_file(), str(source)
        if ROOT not in source.parents:
            # Runtime executables are prerequisites, not distributable project
            # sources. Verify their identity but never publish the binary.
            observed = pin(source)
            assert observed['sha256'] == expected_sha, str(source)
            assert expected_bytes is None or expected_bytes == observed['bytes'], str(source)
            external_runtime[(str(source), expected_sha)] = {'path': str(source), **observed,
                'export': 'identity metadata only; installed runtime binary excluded'}
            return
        relative = str(source.relative_to(ROOT))
        replacement = historical_sources.get((relative, expected_sha))
        if replacement is not None:
            replacement = Path(replacement)
            assert replacement.is_file() and ROOT in replacement.parents
            observed = pin(replacement)
            overrides[(relative, expected_sha)] = replacement
        else:
            observed = pin(source)
        assert observed['sha256'] == expected_sha, str(source)
        assert expected_bytes is None or expected_bytes == observed['bytes'], str(source)
        identity = (relative, expected_sha)
        if identity in requirements:
            assert requirements[identity] == observed, relative
        requirements[identity] = observed

    def scan(value):
        if isinstance(value, dict):
            if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
                p = Path(value['path'])
                p = p if p.is_absolute() else ROOT / p
                if p.is_file():
                    require(p, value['sha256'], value.get('bytes'))
            # Includes activation prerequisites, root receipts and preservation
            # maps without interpreting arbitrary hashes as file names.
            for path, sha in value.items():
                if (isinstance(path, str) and '/' in path and isinstance(sha, str)
                        and len(sha) == 64 and all(c in '0123456789abcdef' for c in sha)):
                    candidate = Path(path)
                    candidate = candidate if candidate.is_absolute() else ROOT / candidate
                    if candidate.is_file():
                        require(candidate, sha)
            for part in value.values():
                scan(part)
        elif isinstance(value, list):
            for part in value:
                scan(part)

    for folder, label, exclusions in folders:
        folder = ROOT / folder
        if not folder.exists():
            continue
        for p in sorted(folder.rglob('*')):
            if not p.is_file() or p.suffix not in ('.json', '.py', '.zip', '.txt', '.md', '.gz', '.diff'):
                continue
            if '__pycache__' in p.parts or p.name in exclusions:
                continue
            relative = label + '/' + str(p.relative_to(folder))
            target = DEST / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
            published_path = str(target.relative_to(ROOT))
            origins.append({'origin': str(p.relative_to(ROOT)), 'path': published_path, **pin(p)})
            files.add(published_path)
            require(p, pin(p)['sha256'])
            if p.suffix == '.json':
                scan(load(p))

    # These established routes already bind the unchanged historical sources.
    old_routes = {}
    archive_cache = {}
    for p in sorted((PUB / 'docs/research/gcts-rl-renewal').rglob('*.json')):
        if p.name not in ('origins.json', 'source-input-bindings.json'):
            continue
        records = load(p)
        if not isinstance(records, list):
            continue
        for e in records:
            if not isinstance(e, dict) or 'sha256' not in e:
                continue
            origin = e.get('origin') or e.get('path')
            published = e.get('path') if e.get('origin') else e.get('published_path')
            # The staged successor is not an established historical route.
            # Reusing its archive while regenerating would omit its own members.
            if not published or published.startswith(PREFIX):
                continue
            target = PUB / published
            member = e.get('archive_member')
            if not target.is_file():
                continue
            if member:
                if published not in archive_cache:
                    archive_cache[published] = zipfile.ZipFile(target)
                try:
                    data = archive_cache[published].read(member)
                except KeyError:
                    continue
                observed = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
            else:
                observed = pin(target)
            if observed['sha256'] == e['sha256'] and e.get('bytes', observed['bytes']) == observed['bytes']:
                old_routes[(origin, e['sha256'])] = {'published_path': published, 'archive_member': member}

    new_routes = {e['origin']: {'published_path': e['path'], 'archive_member': None} for e in origins}
    bindings = []
    archive = DEST / 'sources-and-inputs.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for (path, version), expected in sorted(requirements.items()):
            identity = (path, version)
            direct = new_routes.get(path)
            if direct and pin(ROOT / path) != expected:
                direct = None
            route = None if identity in overrides else direct or old_routes.get(identity)
            if identity not in overrides and route is None and (PUB / path).is_file() and pin(PUB / path) == expected:
                route = {'published_path': path, 'archive_member': None}
            if route is None:
                member = ('historical/' + version + '/' + path
                          if identity in overrides else path)
                z.write(overrides.get(identity, ROOT / path), member)
                route = {'published_path': str(archive.relative_to(ROOT)), 'archive_member': member}
            bindings.append({'path': path, **expected, **route})
    files.add(str(archive.relative_to(ROOT)))
    for z in archive_cache.values():
        z.close()
    for name, records in [('source-input-bindings.json', bindings), ('origins.json', origins),
                          ('external-runtime-bindings.json', [external_runtime[k] for k in sorted(external_runtime)])]:
        path = DEST / name
        path.write_text(json.dumps(records, indent=2) + '\n')
        files.add(str(path.relative_to(ROOT)))
    return files, origins, bindings
