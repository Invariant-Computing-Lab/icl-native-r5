"""Create a versioned, content-hashed R5 archive; never upload or execute it.
Run only on a complete R5 source tree. The generated ZIP is outside the tree.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def selected(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if path.is_symlink():
        raise ValueError(f"Symlink refused: {rel}")
    if not path.is_file() or rel.as_posix() == 'MANIFEST.json':
        return False
    return not (set(rel.parts) & {'__pycache__', '.pytest_cache', 'build', 'local_runs'}
                or any(s.endswith('.egg-info') for s in rel.parts))

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def main(destination: Path) -> dict:
    destination = destination.resolve()
    if destination == ROOT or ROOT in destination.parents:
        raise ValueError('Archive must be outside the source tree')
    if destination.exists():
        raise FileExistsError('Refusing to overwrite an existing release ZIP')
    files = sorted(p for p in ROOT.rglob('*') if selected(p))
    manifest = {
        'schema': 'ICL_R5_RELEASE_MANIFEST/1',
        'release_id': 'ICL_R5_20261013',
        'language_version': '0.2.1',
        'origin': 'new implementation and training on preserved original core',
        'scope': 'bounded semantic opcode model and local console, not general source synthesis',
        'drive_upload': 'NOT_PERFORMED',
        'hash_scope': 'delivery integrity, not authorship, safety certification or scientific validity',
        'excluded_transient_paths': ['__pycache__', '.pytest_cache', 'build', '*.egg-info', 'local_runs'],
        'files': {p.relative_to(ROOT).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in files},
    }
    (ROOT / 'MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    files.append(ROOT / 'MANIFEST.json')
    with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(files):
            info = zipfile.ZipInfo('ICL_R5_20261013/' + path.relative_to(ROOT).as_posix(), (2026, 10, 13, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, path.read_bytes())
    return {'archive': destination.name, 'bytes': destination.stat().st_size,
            'sha256': digest(destination), 'manifest_payload_files': len(manifest['files'])}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    print(json.dumps(main(parser.parse_args().destination), indent=2))
