from pathlib import Path
import subprocess,tempfile,sys,json
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'source'),str(R/'source/icl_core')]
import numpy as np,torch
from icl_native.common import *
from icl_native.checkpoint import load_checkpoint
out=R/'reports/trained_logits_reload';out.mkdir(exist_ok=True);rows=[]
for i,intent in enumerate(INTENTS):
 flags={k:True for k in FLAGS}
 if intent=='translate':flags['observer_match']=False
 if intent=='restore':flags['witness_valid']=False
 if intent=='journal':flags['journal_allowed']=False
 s={'intent':intent,'arg':i%7-3,'modulus':2+i%10,'flags':flags};rows.append(features(s,[-100000,-1,0,1,100000][i%5],i%2==0))
X=np.asarray(rows,dtype=np.float32);dump(out/'fixtures.json',X.astype(float).tolist());m,meta=load_checkpoint(R/'models/native_17/best');torch.set_num_threads(1)
with torch.no_grad():expected=m(torch.from_numpy(X)).numpy()
venv=Path(tempfile.mkdtemp(prefix='icl-logits-'));subprocess.run([sys.executable,'-m','venv',str(venv)],check=True,capture_output=True);py=venv/'bin/python'
subprocess.run([str(py),'-m','pip','install','--no-index','--no-deps',str(R/'source/icl_core/dist/invariant_cognition_language-0.2.1-py3-none-any.whl')],check=True,capture_output=True)
script=out/'probe.py';script.write_text('''import sys,json,importlib.util\nfrom pathlib import Path\nr=Path(sys.argv[1]);assert importlib.util.find_spec('torch') is None and importlib.util.find_spec('numpy') is None\nimport icl\nassert 'site-packages' in icl.__file__\ndef audit(e,a):\n if e.startswith('socket.'):raise PermissionError('NETWORK_BLOCKED')\nsys.addaudithook(audit)\nsys.path.insert(0,str(r/'source'))\nfrom icl_native.offline_infer import OfflineModel\nm=OfflineModel(r/'models/offline_native_17');rows=json.loads((r/'reports/trained_logits_reload/fixtures.json').read_text());out=[m.logits(row) for row in rows];print(json.dumps(out))\n''')
p=subprocess.run([str(py),'-I',str(script),str(R)],text=True,capture_output=True,timeout=30);(out/'probe.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr;actual=np.asarray(json.loads(p.stdout))
np.testing.assert_allclose(actual,expected,rtol=1e-5,atol=1e-5)
dump(out/'SUMMARY.json',{'status':'PASS','fixture_rows':len(rows),'logits_per_row':22,'max_abs_error':float(np.max(np.abs(actual-expected))),'atol':1e-5,'rtol':1e-5,'same_argmax':bool(np.all(actual.argmax(-1)==expected.argmax(-1))),'boundary':'trained float32 Torch checkpoint vs exported weights executed by installed ICL Float64 VM in a new standard-library-only process','new_process_without_torch_numpy':True,'checkpoint_sha256':sha(R/'models/native_17/best/weights.safetensors')});print('TRAINED_LOGIT_PARITY_PASS',float(np.max(np.abs(actual-expected))))
