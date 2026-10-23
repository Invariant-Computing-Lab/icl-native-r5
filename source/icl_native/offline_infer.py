"""Standard-library inference with real trained weights evaluated by the ICL VM.
No Torch, NumPy, network API, label oracle or training object is needed.
The native model selects finite semantic opcodes, not unrestricted source text.
"""
from __future__ import annotations
import argparse,copy,json,math,sys
from pathlib import Path
from .common import ACTIONS,ERRORS,FEATURE_NAMES,features,strict_load,dump,sha,canonical
from .execution import validate_plan,protocol_guard,advance_runtime,vm_verify
from icl.api import run_ocir,loads_ocir,SCHEMA_VERSION,SCHEMA_SHA256
from icl.runtime import ICLError
import icl
SHAPES={'w1':[30,32],'b1':[1,32],'w2':[32,32],'b2':[1,32],'wo':[32,22],'bo':[1,22]}
class OfflineModel:
 def __init__(self,path:Path):
  if not path.is_dir():raise ValueError('MODEL_NOT_LOADED')
  man=strict_load(path/'manifest.json',200000)
  if man.get('schema')!='ICL_R5_OFFLINE_BUNDLE/1' or set(man.get('files',{}))!={'weights.json','compiled_model.ocir','model.icl','model_config.json'}:raise ValueError('BUNDLE_SCHEMA')
  for n,m in man['files'].items():
   p=path/n
   if p.is_symlink() or not p.is_file() or p.stat().st_size!=m['bytes'] or p.stat().st_size>2_000_000 or sha(p)!=m['sha256']:raise ValueError('MODEL_INTEGRITY')
  core=Path(icl.__file__).parent
  if set(man['runtime_file_hashes'])!={'__init__.py','__main__.py','api.py','checker.py','cli.py','frontend.py','interpreter.py','legacy_afc.py','runtime.py','vm.py','OCIR_SCHEMA.json','TOKEN_VOCAB.json'}:raise ValueError('RUNTIME_LOCK_SCHEMA')
  if any(sha(core/n)!=h for n,h in man['runtime_file_hashes'].items()):raise ValueError('RUNTIME_INCOMPATIBLE')
  cfg=strict_load(path/'model_config.json');self.cfg=cfg
  if cfg['actions']!=ACTIONS or cfg['feature_names']!=FEATURE_NAMES or cfg['schema_version']!=SCHEMA_VERSION or cfg['schema_sha256']!=SCHEMA_SHA256:raise ValueError('MODEL_CONTRACT')
  self.weights=strict_load(path/'weights.json',500000)
  if set(self.weights)!=set(SHAPES):raise ValueError('WEIGHT_KEYS')
  for k,v in self.weights.items():
   if set(v)!={'shape','data'} or v['shape']!=SHAPES[k] or len(v['data'])!=math.prod(SHAPES[k]) or any(type(x) not in (float,int) or not math.isfinite(x) for x in v['data']):raise ValueError('WEIGHT_SHAPE_OR_FINITE')
  self.graph=loads_ocir((path/'compiled_model.ocir').read_text())
 def logits(self,row):
  if len(row)!=30 or any(not math.isfinite(v) for v in row):raise ValueError('FEATURE_INPUT')
  out=run_ocir(self.graph,args=[{'shape':[1,30],'data':row}]+[self.weights[k] for k in SHAPES],engine='vm')
  return out['value']['data']
 def predict(self,plan,journal_permission=False):
  validate_plan(plan);x=plan['initial'];mem=plan['memory'];actions=[];conf=[];guard=None;result=None;attempts=0;allow=0
  for j,s0 in enumerate(plan['steps']):
   s=copy.deepcopy(s0);s['flags']['journal_allowed']=journal_permission is True and s['flags']['journal_allowed'] is True
   logits=self.logits(features(s,x,mem is not None));m=max(logits);den=sum(math.exp(v-m) for v in logits);a=max(range(len(logits)),key=lambda k:logits[k]);act=ACTIONS[a]
   actions.append(act);conf.append(math.exp(logits[a]-m)/den)
   if act in ERRORS:result={'tag':'Err','error':act};break
   if act=='JOURNAL':attempts+=1
   err=protocol_guard(act,s0,mem,journal_permission)
   if err:guard={'step':j,'reason':err};result={'tag':'Err','error':err};break
   try:x,mem=advance_runtime(act,x,s0['arg'],mem)
   except (ICLError,OverflowError,ValueError) as e:
    reason=getattr(e,'code',str(e));guard={'step':j,'reason':reason};result={'tag':'Err','error':reason};break
   if act=='JOURNAL':allow+=1
  return {'actions':actions,'confidence':min(conf) if conf else 0.0,'composed_result':result or {'tag':'Ok','value':x},'guard_rejection':guard,'journal_attempts':attempts,'journal_allow_decisions':allow,'execution_scope':'host simulation until vm_verify executes the candidate'}
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--permit-local-journal',action='store_true');a=p.parse_args(argv)
 try:
  m=OfflineModel(a.model);req=strict_load(a.request,100000);pred=m.predict(req,a.permit_local_journal);v=vm_verify(req,pred,a.permit_local_journal)
  answer={'schema':'ICL_R5_PRODUCT_RESULT/1','model_seed':m.cfg['seed'],'proposal':pred,'verification':v,'scope':'finite structured intent -> learned opcode -> deterministic ICL code and VM','learned':'opcode and finite error-class decision','not_learned':'source syntax, composition control, exact arithmetic, authoritative permission, persistent memory','confidence_is_uncalibrated':True,'tensor_backend':'ICL VM pure Python float64','third_party_weights_used':False}
  if a.output:dump(a.output,answer)
  print(canonical(answer));return 0
 except Exception as e:
  print(canonical({'status':'ERROR','error_type':type(e).__name__,'reason':str(e)}),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
