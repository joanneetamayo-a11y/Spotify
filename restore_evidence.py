"""Restore saved evidence offline, checking archive and file SHA-256 hashes."""
from pathlib import Path
import hashlib, io, json, tarfile
root = Path(__file__).resolve().parent
manifest = json.loads((root / 'evidence-manifest.json').read_text())
packed = b''.join((root / part).read_bytes() for part in manifest['parts'])
if hashlib.sha256(packed).hexdigest() != manifest['archive_sha256']:
    raise SystemExit('Archive checksum mismatch; download all evidence parts again.')
expected = {e['path']: e for e in manifest['files']}
restored = set()
with tarfile.open(fileobj=io.BytesIO(packed), mode='r|xz') as archive:
    for member in archive:
        if member.name not in expected or not member.isfile():
            raise SystemExit('Unexpected archive entry: ' + member.name)
        target = (root / member.name).resolve()
        if not target.is_relative_to(root):
            raise SystemExit('Unsafe archive path')
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.restore-tmp')
        digest = hashlib.sha256()
        with archive.extractfile(member) as source, temporary.open('wb') as out:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
                out.write(chunk)
        if digest.hexdigest() != expected[member.name]['sha256']:
            temporary.unlink()
            raise SystemExit('File checksum mismatch: ' + member.name)
        temporary.replace(target)
        restored.add(member.name)
if restored != set(expected):
    raise SystemExit('Archive is missing expected files.')
print(f'Restored and SHA-256 verified {len(restored)} evidence files. No API calls made.')
