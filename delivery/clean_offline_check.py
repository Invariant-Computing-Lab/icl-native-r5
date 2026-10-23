"""Exercise new wheel and trained weights in an isolated, no-third-party venv.
Network blocking below is Python audit-hook blocking, not OS namespace isolation.
"""
from pathlib import Path
import subprocess,json,sys,os,tempfile,time,hashlib
R=Path(__file__).resolve().parents[1];out=R/'reports/clean_offline';out.mkdir(parents=True,exist_ok=True)
venv=Path(tempfile.mkdtemp(prefix='icl-r5-venv-'));subprocess.run([sys.executable,'-m','venv',str(venv)],check=True,capture_output=True)
py=venv/'bin/python';whl=R/'source/icl_core/dist/invariant_cognition_language-0.2.1-py3-none-any.whl'
install=subprocess.run([str(py),'-m','pip','install','--no-index','--no-deps',str(whl)],text=True,capture_output=True);(out/'install.log').write_text(install.stdout+install.stderr);assert install.returncode==0
launcher=out/'launcher.py'
launcher.write_text('''import sys,json,importlib.util\nfrom pathlib import Path\nsource=Path(sys.argv.pop(1));request=Path(sys.argv.pop(1));output=Path(sys.argv.pop(1));permit=sys.argv.pop(1)=='yes'\nassert importlib.util.find_spec('torch') is None\nassert importlib.util.find_spec('numpy') is None\nimport icl\nassert 'site-packages' in icl.__file__\ndef audit(event,args):\n if event.startswith('socket.'):raise PermissionError('NETWORK_BLOCKED_BY_PYTHON_AUDIT')\nsys.addaudithook(audit)\nimport socket\ntry:socket.socket();raise AssertionError('socket permitted')\nexcept PermissionError:pass\nsys.path.insert(0,str(source/'source'))\nfrom icl_native.offline_infer import main\nrc=main(['--model',str(source/'models/offline_native_17'),'--request',str(request),'--output',str(output)]+(['--permit-local-journal'] if permit else []))\nassert not any(k=='torch' or k.startswith('numpy') for k in sys.modules)\nraise SystemExit(rc)\n''')
checks=[]
for name,permit,expected in [('demo',False,{'tag':'Ok','value':-4}),('denied_journal',False,{'tag':'Err','error':'EFFECT_DENIED'}),('denied_journal',True,{'tag':'Ok','value':5}),('missing_witness',False,{'tag':'Err','error':'NON_IDENTIFIABLE'}),('wrong_observer',False,{'tag':'Err','error':'OBSERVER_MISMATCH'}),('missing_memory',False,{'tag':'Err','error':'MEMORY_MISSING'})]:
 tag=name+('_permit' if permit else '');target=out/(tag+'.json');cmd=[str(py),'-I',str(launcher),str(R),str(R/'examples'/f'{name}.json'),str(target),'yes' if permit else 'no'];start=time.time()
 p=subprocess.run(cmd,cwd='/tmp',text=True,capture_output=True,timeout=30);(out/(tag+'.log')).write_text(p.stdout+p.stderr)
 assert p.returncode==0,(tag,p.stderr);a=json.loads(target.read_text());v=a['verification'];assert v['executed'] and v['runtime_consistency'] and v['result']['value']==expected
 effects=v['result']['effects'];assert all(e['external_executed'] is False for e in effects)
 if not permit:assert not effects
 checks.append({'name':tag,'command':cmd,'exit_code':p.returncode,'expected_result':expected,'actual_result':v['result']['value'],'actual_effect_events':effects,'elapsed_seconds':time.time()-start,'status':'PASS'})
# Fresh-process checkpoint persistence tests run installed core, not source import.
replay=out/'replay_probe.py'
replay.write_text('''import sys,json\nfrom pathlib import Path\nfrom icl.api import compile_source,run_ocir,dumps_ocir,loads_ocir\np=Path(sys.argv[2]);mode=sys.argv[1]\nif mode=='save':\n s='module test; fn main()->Int64 {var x=0; while x<4 limit 4 {x=x+1;} return x;}'\n o=compile_source(s);p.with_suffix('.ocir').write_text(dumps_ocir(o));a=run_ocir(o,stop_after=6);p.write_text(json.dumps(a['checkpoint']));p.with_suffix('.full').write_text(json.dumps(run_ocir(o)))\nelse:\n o=loads_ocir(p.with_suffix('.ocir').read_text());a=run_ocir(o,checkpoint=json.loads(p.read_text()));b=json.loads(p.with_suffix('.full').read_text());assert a['value']==b['value'] and a['trace']==b['trace'];print('SEPARATE_PROCESS_REPLAY_PASS')\n''')
for mode in ['save','load']:
 p=subprocess.run([str(py),'-I',str(replay),mode,str(out/'checkpoint.json')],cwd='/tmp',text=True,capture_output=True,timeout=20);(out/('replay_'+mode+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
 checks.append({'name':'installed_core_checkpoint_'+mode,'exit_code':p.returncode,'status':'PASS'})
summary={'checks':checks,'passed':len(checks),'wheel_sha256':hashlib.sha256(whl.read_bytes()).hexdigest(),'runtime_dependencies':'Python standard library and installed ICL wheel only; no numpy or torch discoverable','model_weights':'actual selected seed17 exported weights, not static answers','network_control':'Python audit-hook rejection tested; no OS network namespace claim','fresh_process_per_example':True,'note':'Local journal is an in-memory simulator, no external operation is installed.'}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print('CLEAN_OFFLINE_PASS',len(checks))
