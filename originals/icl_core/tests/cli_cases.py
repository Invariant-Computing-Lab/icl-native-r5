"""Real subprocess CLI checks, including hostile file inputs. Never invokes network."""
import json,os,pathlib,subprocess,sys,tempfile,zipfile
from run_acceptance import ROOT

def run_cli_cases():
    records=[]
    with tempfile.TemporaryDirectory(prefix='icl-cli-e2e-') as directory:
        d=pathlib.Path(directory);env=dict(os.environ);env['PYTHONPATH']=str(ROOT)
        def call(name,args,predicate,expected_code=0):
            r=subprocess.run([sys.executable,'-m','icl',*map(str,args)],cwd=d,env=env,capture_output=True,text=True,timeout=30)
            rec={'id':name,'family':'cli','command':['python','-m','icl',*map(str,args)],'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
            try:rec['passed']=r.returncode==expected_code and predicate(r)
            except Exception as e:rec['passed']=False;rec['assertion_error']=str(e)
            records.append(rec);return r
        src=d/'program.icl';src.write_text('module e2e; fn main() -> Int64 { var n: Int64 = random_int(50); var i: Int64 = 0; while i < 4 limit 8 { n = n + random_int(50); i = i + 1; } return n; }')
        ir=d/'program.ocir.json';cp=d/'checkpoint.json'
        for command in ('check','run','compile','inspect','replay','test'):
            call('cli_help_'+command,[command,'--help'],lambda r:'usage:' in r.stdout and not r.stderr)
        call('cli_check',[ 'check',src,'--json'],lambda r:json.loads(r.stdout)['status']=='PASS' and not r.stderr)
        full=call('cli_run_vm',['run',src,'--json','--trace'],lambda r:json.loads(r.stdout)['halted'] is True and not r.stderr)
        fullval=json.loads(full.stdout)['value']
        call('cli_run_tree',['run',src,'--engine','tree','--json'],lambda r:json.loads(r.stdout)['value']==fullval)
        call('cli_compile',['compile',src,'-o',ir,'--json'],lambda r:json.loads(r.stdout)['status']=='PASS' and ir.is_file())
        call('cli_inspect',['inspect',ir,'--json'],lambda r:json.loads(r.stdout)['integrity']=='PASS')
        call('cli_pause',['run',src,'--stop-after','12','--checkpoint-out',cp,'--json'],lambda r:json.loads(r.stdout)['status']=='PAUSED' and cp.is_file())
        call('cli_replay',['replay',ir,cp,'--json','--trace'],lambda r:json.loads(r.stdout)['value']==fullval and json.loads(r.stdout)['trace']==json.loads(full.stdout)['trace'])
        call('cli_smoke_test',['test','--json'],lambda r:json.loads(r.stdout)['status']=='PASS')
        invalid=d/'invalid.icl';invalid.write_text('module bad;\nfn main() -> Int64 {\nreturn true;\n}')
        call('cli_error_stderr_and_exit',['check',invalid,'--json'],lambda r:not r.stdout and json.loads(r.stderr)['diagnostic']['code']=='TYPE' and json.loads(r.stderr)['diagnostic']['span']['line']==3,2)
        modules=d/'modules.json';modules.write_text(json.dumps({'mathlib':'module mathlib; fn f(x:Int64)->Int64{return x*3;}'}))
        multi=d/'multi.icl';multi.write_text('module multi; import mathlib; fn main()->Int64{return mathlib.f(5);}')
        call('cli_explicit_module_map',['run',multi,'--module-map',modules,'--json'],lambda r:json.loads(r.stdout)['value']==15)
        link=d/'symlink.icl';link.symlink_to(src)
        call('cli_symlink_input_rejected',['run',link,'--json'],lambda r:not r.stdout and json.loads(r.stderr)['diagnostic']['code']=='PATH',2)
        archive=d/'hostile.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('../../escaped.txt','x'*8000000)
        call('cli_archive_bomb_not_extracted',['check',archive,'--json'],lambda r:not r.stdout and json.loads(r.stderr)['diagnostic']['code'] in ('PATH','LEX') and not (d/'escaped.txt').exists(),2)
        badcp=d/'badcp.json';badcp.write_text(cp.read_text().replace('"prng":','"prng":999,"oldprng":',1))
        call('cli_corrupt_checkpoint_rejected',['replay',ir,badcp,'--json'],lambda r:not r.stdout and json.loads(r.stderr)['diagnostic']['code']=='CHECKPOINT_CORRUPT',2)
    return records
