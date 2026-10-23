from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'));sys.path.insert(0,str(R/'source/icl_core'))
import torch
from icl_native.common import *
from icl_native.graph import model_source
from icl_native.checkpoint import load_checkpoint
from icl.api import compile_source,dumps_ocir,SCHEMA_VERSION,SCHEMA_SHA256
p=R/'models/offline_native_17';p.mkdir(exist_ok=True)
m,meta=load_checkpoint(R/'models/native_17/best');dump(p/'weights.json',{k:{'shape':list(v.shape),'data':[float(x) for x in v.detach().flatten()]} for k,v in m.named_parameters()})
(p/'model.icl').write_text(model_source());(p/'compiled_model.ocir').write_text(dumps_ocir(compile_source(model_source())))
dump(p/'model_config.json',{'seed':17,'choice':'preselected first seed, not selected on held-out outcomes','actions':ACTIONS,'feature_names':FEATURE_NAMES,'schema_version':SCHEMA_VERSION,'schema_sha256':SCHEMA_SHA256,'parameters':meta['parameter_count'],'base_model':None,'source_checkpoint_sha256':sha(R/'models/native_17/best/weights.safetensors'),'scope':'bounded opcode classifier, deterministic composer/emitter/executor'})
core=R/'source/icl_core/icl';names=['__init__.py','__main__.py','api.py','checker.py','cli.py','frontend.py','interpreter.py','legacy_afc.py','runtime.py','vm.py','OCIR_SCHEMA.json','TOKEN_VOCAB.json']
dump(p/'manifest.json',{'schema':'ICL_R5_OFFLINE_BUNDLE/1','files':{n:{'bytes':(p/n).stat().st_size,'sha256':sha(p/n)} for n in ['weights.json','compiled_model.ocir','model.icl','model_config.json']},'runtime_file_hashes':{n:sha(core/n) for n in names},'security':'Hash detects accidental/tampered-content mismatch, not publisher authentication or OS sandbox certification.'})
print('exported',p,sum(q.stat().st_size for q in p.iterdir()))
