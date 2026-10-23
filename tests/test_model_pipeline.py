import sys,copy,json,shutil
from pathlib import Path
import numpy as np
import pytest,torch
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
from icl_native.common import *
from icl_native.graph import Native,model_source
from icl_native.checkpoint import load_checkpoint
from icl_native.product import *
from icl.api import run_ocir,compile_source

def as_icl(v):a=v.detach().cpu().numpy();return {'shape':list(a.shape),'data':[float(x) for x in a.ravel()]}
@pytest.mark.parametrize('seed',[3,9,15,21])
def test_graph_forward(seed):
 torch.manual_seed(seed);m=Native().double();x=torch.randn(1,D,dtype=torch.float64)
 a=run_ocir(m.graph,args=[as_icl(x)]+[as_icl(v) for v in m.parameters()])['value']['data'];b=m(x).detach().numpy().ravel()
 np.testing.assert_allclose(a,b,rtol=1e-9,atol=1e-10)
def test_gradient_icl_finite_difference():
 torch.manual_seed(91);m=Native().double();x=torch.randn(1,D,dtype=torch.float64);m(x).sum().backward();eps=1e-5
 checked=[]
 for p in m.parameters():
  for i in [0,p.numel()-1]:
   analytic=float(p.grad.view(-1)[i]);values=[];old=float(p.detach().view(-1)[i])
   for delta in (eps,-eps):
    with torch.no_grad():p.view(-1)[i]=old+delta
    values.append(sum(run_ocir(m.graph,args=[as_icl(x)]+[as_icl(v) for v in m.parameters()])['value']['data']))
   with torch.no_grad():p.view(-1)[i]=old
   numeric=(values[0]-values[1])/(2*eps);assert abs(analytic-numeric)<1e-7;checked.append(abs(analytic-numeric))
 dump(R/'reports/GRADIENT_PARITY.json',{'passed_coordinates':len(checked),'max_abs_error':max(checked),'method':'central finite differences of actual ICL interpreter forward vs host autograd, float64','epsilon':eps})
@pytest.mark.parametrize('kind',['native','flat','no_context','no_witness','no_memory','no_invariance'])
@pytest.mark.parametrize('seed',[17,29,43])
def test_reload(kind,seed):
 m,meta=load_checkpoint(R/'models'/f'{kind}_{seed}'/'best');assert meta['parameter_count']==sum(p.numel() for p in m.parameters());assert torch.isfinite(m(torch.zeros(2,D))).all()
def test_corruption_rejected(tmp_path):
 p=tmp_path/'m';shutil.copytree(R/'models/native_17/best',p)
 f=p/'weights.safetensors';b=bytearray(f.read_bytes());b[-1]^=1;f.write_bytes(b)
 with pytest.raises(ValueError,match='CHECKPOINT_INTEGRITY'):load_checkpoint(p)
def test_schema_forged_even_with_rehashed_manifest(tmp_path):
 p=tmp_path/'m';shutil.copytree(R/'models/native_17/best',p);f=p/'state.json';m=json.loads(f.read_text());m['schema_version']='wrong';dump(f,m)
 man=json.loads((p/'manifest.json').read_text());man['files']['state.json']={'sha256':sha(f),'bytes':f.stat().st_size};dump(p/'manifest.json',man)
 with pytest.raises(ValueError,match='SCHEMA_INCOMPATIBLE'):load_checkpoint(p)
def test_empty_checkpoint(tmp_path):
 with pytest.raises((ValueError,FileNotFoundError)):load_checkpoint(tmp_path)
@pytest.mark.parametrize('v',['true',1,None])
def test_strict_bool_flags(v):
 p={'initial':2,'memory':None,'steps':[{'intent':'journal','arg':1,'modulus':3,'flags':{k:True for k in FLAGS}}]};p['steps'][0]['flags']['journal_allowed']=v
 with pytest.raises(ValueError):validate_plan(p)
def test_no_oracle_in_production(monkeypatch):
 import icl_native.common as c
 monkeypatch.setattr(c,'oracle_action',lambda *a:(_ for _ in ()).throw(AssertionError('oracle_called')))
 m,meta=load_checkpoint(R/'models/native_17/best')
 p={'initial':2,'memory':None,'steps':[{'intent':'increase','arg':1,'modulus':3,'flags':{k:True for k in FLAGS}}]}
 q=predict_many(m,[p])[0];v=vm_verify(p,q);assert v['executed'] and v['runtime_consistency']
@pytest.mark.parametrize('host_permission',[False,'true',1,None])
def test_authority_never_model_granted(host_permission):
 s={'intent':'journal','arg':0,'modulus':3,'flags':{k:True for k in FLAGS}}
 assert protocol_guard('JOURNAL',s,None,host_permission)=='EFFECT_DENIED'
def test_memory_absent_rejected():
 s={'intent':'recall','arg':0,'modulus':3,'flags':{k:True for k in FLAGS}}
 assert protocol_guard('RECALL',s,None,False)=='MEMORY_MISSING'
def test_witness_missing_rejected():
 s={'intent':'restore','arg':0,'modulus':3,'flags':{k:True for k in FLAGS}};s['flags']['witness_present']=False
 assert protocol_guard('RESTORE',s,None,False)=='NON_IDENTIFIABLE'

def test_int64_min_abs_rejected():
 with pytest.raises(ICLError):advance_runtime('ABS',-(1<<63),0,None)
def test_offline_numeric_overflow_matches_online():
 from icl_native.offline_infer import OfflineModel
 p={'initial':100000,'memory':None,'steps':[{'intent':'scale','arg':3,'modulus':7,'flags':{k:True for k in FLAGS}} for _ in range(32)]}
 a=OfflineModel(R/'models/offline_native_17').predict(p);m,meta=load_checkpoint(R/'models/native_17/best');b=predict_many(m,[p])[0]
 assert a['composed_result']==b['composed_result'] and a['guard_rejection']==b['guard_rejection'] and a['guard_rejection'] is not None

def test_strict_json_exponent_overflow(tmp_path):
 p=tmp_path/'a.json';p.write_text('{"x":1e999}')
 with pytest.raises(ValueError,match='NONFINITE'):strict_load(p)

def test_optimizer_npz_unknown_member_rejected(tmp_path):
 import zipfile
 p=tmp_path/'m';shutil.copytree(R/'models/native_17/final',p)
 with zipfile.ZipFile(p/'optimizer.npz','a') as z:z.writestr('unexpected.npy',b'bad')
 man=strict_load(p/'manifest.json');man['files']['optimizer.npz']={'bytes':(p/'optimizer.npz').stat().st_size,'sha256':sha(p/'optimizer.npz')};dump(p/'manifest.json',man)
 with pytest.raises(ValueError,match='OPTIMIZER_ARCHIVE_LIMIT_OR_SCHEMA'):load_checkpoint(p,with_optimizer=True)

def test_parameter_count_mismatch_rejected(tmp_path):
 p=tmp_path/'m';shutil.copytree(R/'models/native_17/final',p);meta=strict_load(p/'state.json');meta['parameter_count']=0;dump(p/'state.json',meta)
 man=strict_load(p/'manifest.json');man['files']['state.json']={'bytes':(p/'state.json').stat().st_size,'sha256':sha(p/'state.json')};dump(p/'manifest.json',man)
 with pytest.raises(ValueError,match='PARAMETER_COUNT_MISMATCH'):load_checkpoint(p)
