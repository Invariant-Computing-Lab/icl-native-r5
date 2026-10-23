from pathlib import Path,PurePosixPath
import json,hashlib,zipfile,shutil,stat
root=Path(__file__).parent
p=Path('/mnt/data/icl_recovery/originals/ICL_CORE_v0.1.0_20261010.zip')
z=zipfile.ZipFile(p); names=z.namelist()
assert len(set(names))==len(names)
assert sum(i.file_size for i in z.infolist())<20000000
for i in z.infolist():
 q=PurePosixPath(i.filename)
 assert not q.is_absolute() and '..' not in q.parts and '\\' not in i.filename
 assert not stat.S_ISLNK(i.external_attr>>16)
manifest=json.loads(z.read('icl_core/MANIFEST.json'))
for f in manifest['files']:
 b=z.read('icl_core/'+f['path']); assert len(b)==f['bytes']; assert hashlib.sha256(b).hexdigest()==f['sha256']
z.extractall(root/'originals')
shutil.copy2(p,root/'originals'/p.name)
shutil.copytree(root/'originals'/'icl_core',root/'source'/'icl_core',dirs_exist_ok=True)
r={'archive_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'archive_bytes':p.stat().st_size,'manifest_verified_entries':len(manifest['files']),'original_member_count':len(names),'origin':'Drive persisted original ICL-Core 0.1.0','original_commit':manifest['code_commit'],'unchanged_originals':True,'R4_original_model_recovered':False}
(root/'reports'/'BASELINE_LOCK.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2))
