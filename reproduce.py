"""Re-run checks, or explicitly retrain in a NEW directory without modifying weights.
No dependency installations, downloads or Drive writes are performed here.
"""
from pathlib import Path
import argparse,subprocess,sys,os,json,tempfile,shutil,time
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--retrain-in',type=Path);p.add_argument('--full-ast-audit',action='store_true');args=p.parse_args()
if args.retrain_in:
 root=args.retrain_in.resolve()
 if root.exists():raise SystemExit('Refusing existing destination; choose a new empty/nonexistent directory.')
 root.mkdir(parents=True);shutil.copytree(R/'source',root/'source');shutil.copytree(R/'data',root/'data');(root/'reports').mkdir();shutil.copy2(R/'reports/PRECOMMITTED_PROTOCOL.json',root/'reports/PRECOMMITTED_PROTOCOL.json')
 cmd=[sys.executable,'-m','icl_native.train'];env=os.environ|{'PYTHONPATH':str(root/'source')+os.pathsep+str(root/'source/icl_core'),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
 raise SystemExit(subprocess.run(cmd,cwd=root,env=env).returncode)
# All checks write into a fresh copy, preserving the delivered manifest and evidence.
original=R;R=Path(tempfile.mkdtemp(prefix='icl-r5-reproduce-copy-'))/'project';shutil.copytree(original,R,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','local_runs','build','*.egg-info'))
out=Path(tempfile.mkdtemp(prefix='icl-r5-reproduce-'));env=os.environ|{'PYTHONPATH':str(R/'source')+os.pathsep+str(R/'source/icl_core'),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
checks=[('unit',R,[sys.executable,'-m','pytest','tests','-q']),('core',R/'source/icl_core',[sys.executable,'tests/run_acceptance.py']),('vm_replay',R/'source/icl_core',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_vm_replay.py','-v']),('offline',R,[sys.executable,str(R/'delivery/clean_offline_check.py')]),('console',R,[sys.executable,str(R/'delivery/check_console.py')])]
checks.append(('trained_logits',R,[sys.executable,str(R/'delivery/check_trained_logits.py')]))
if args.full_ast_audit:checks.append(('generic_ast_audit',R,[sys.executable,str(R/'delivery/audit_reference_asts.py')]))
results=[]
for name,cwd,cmd in checks:
 start=time.time();run=subprocess.run(cmd,cwd=cwd,env=env,text=True,capture_output=True,timeout=600);(out/(name+'.log')).write_text(run.stdout+run.stderr);results.append({'name':name,'command':cmd,'exit_code':run.returncode,'elapsed_seconds':time.time()-start});print(name,run.returncode,flush=True)
(out/'RESULTS.json').write_text(json.dumps(results,indent=2));print('Fresh reproduction logs:',out)
raise SystemExit(0 if all(x['exit_code']==0 for x in results) else 1)
