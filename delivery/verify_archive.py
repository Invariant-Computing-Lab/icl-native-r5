"""Validate the actual R5 payload, without importing any code from the archive.
Self-supplied hashes detect corruption, not authorship or scientific correctness.
"""
from pathlib import Path,PurePosixPath
import hashlib,json,stat,zipfile,math
PREFIX='ICL_R5_20261013/'
def strict_json(raw):
 def pairs(xs):
  d={}
  for k,v in xs:
   if k in d:raise ValueError('DUPLICATE_JSON_KEY')
   d[k]=v
  return d
 def finite_float(s):
  v=float(s)
  if not math.isfinite(v):raise ValueError('NONFINITE')
  return v
 return json.loads(raw,object_pairs_hook=pairs,parse_float=finite_float,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('NONFINITE')))
def validate(path):
 with zipfile.ZipFile(path) as z:
  infos=z.infolist();names=[i.filename for i in infos]
  if len(names)!=len(set(names)):raise ValueError('DUPLICATE_ARCHIVE_MEMBER')
  if len(names)>20000 or sum(i.file_size for i in infos)>1_000_000_000:raise ValueError('ARCHIVE_SIZE_LIMIT')
  for i in infos:
   p=PurePosixPath(i.filename)
   if p.as_posix()!=i.filename or i.is_dir():raise ValueError('NONCANONICAL_ARCHIVE_MEMBER')
   if not i.filename.startswith(PREFIX) or p.is_absolute() or '..' in p.parts or '\\' in i.filename or ':' in i.filename or stat.S_ISLNK(i.external_attr>>16) or i.flag_bits&1:raise ValueError('UNSAFE_ARCHIVE_MEMBER')
   if i.file_size>250_000_000:raise ValueError('MEMBER_SIZE_LIMIT')
  man=strict_json(z.read(PREFIX+'MANIFEST.json'))
  if man.get('schema')!='ICL_R5_RELEASE_MANIFEST/1' or not isinstance(man.get('files'),dict):raise ValueError('MANIFEST_SCHEMA')
  expected={PREFIX+p for p in man['files']}|{PREFIX+'MANIFEST.json'}
  if set(names)!=expected:raise ValueError('UNEXPECTED_OR_MISSING_MEMBER')
  for p,meta in man['files'].items():
   n=PREFIX+p
   if z.getinfo(n).file_size!=meta['bytes']:raise ValueError('SIZE_MISMATCH:'+p)
   h=hashlib.sha256()
   with z.open(n) as f:
    for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
   if h.hexdigest()!=meta['sha256']:raise ValueError('HASH_MISMATCH:'+p)
  required=['source/icl_core/icl/frontend.py','source/icl_native/graph.py','models/offline_native_17/weights.json','models/native_17/best/weights.safetensors','models/native_29/best/weights.safetensors','models/native_43/best/weights.safetensors','reports/ALL_TRAINING_RUNS.json','reports/EVAL_SUMMARY.json','run_local.py','run_console.py']
  if any(p not in man['files'] or man['files'][p]['bytes']==0 for p in required):raise ValueError('REAL_MODEL_PAYLOAD_MISSING')
  weights=strict_json(z.read(PREFIX+'models/offline_native_17/weights.json'))
  if set(weights)!={'w1','b1','w2','b2','wo','bo'} or sum(len(v.get('data',[])) for v in weights.values())!=2774:raise ValueError('WEIGHT_PAYLOAD_INVALID')
  reports=strict_json(z.read(PREFIX+'reports/ALL_TRAINING_RUNS.json'))
  if len(reports)!=18 or any(not r.get('weights_changed') for r in reports):raise ValueError('TRAINING_RECORD_MISSING')
  return {'payload_files':len(man['files']),'payload_bytes':sum(m['bytes'] for m in man['files'].values()),'model_parameters_offline':2774,'training_records':len(reports),'has_real_r5_payload':True,'scope':'integrity and presence, not publisher authentication or full scientific validation'}
if __name__=='__main__':
 import sys
 print(json.dumps(validate(Path(sys.argv[1])),indent=2))
