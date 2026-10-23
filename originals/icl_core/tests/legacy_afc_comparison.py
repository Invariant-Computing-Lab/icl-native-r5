"""New bounded engineering comparison; does not rerun/change original frozen bank."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from icl import legacy_afc
from icl.runtime import RuntimeContext,builtin

def main():
    cases=[]
    for bits in range(2,11):
        report=legacy_afc.finite_report(bits);m=1<<max(1,bits//2);passed=True
        for x in range(1<<bits):
            ctx=RuntimeContext();r=builtin('observe_mod',[x,m,'finite_afc'],ctx);w=builtin('make_witness',[x,m],ctx);got=builtin('recover',[r,w],ctx)['value']
            expected=legacy_afc.recover_from_quotient(legacy_afc.quotient(x,bits),x//m,bits)
            passed=passed and got==expected==x
        cases.append({'bits':bits,'states':1<<bits,'passed':passed,'source_report':report})
    result={'status':'PASS' if all(c['passed'] for c in cases) else 'FAIL','kind':'NEW_ENGINEERING_COMPARISON','legacy_module_sha256':hashlib.sha256(Path(legacy_afc.__file__).read_bytes()).hexdigest(),'cases':cases,'total_states':sum(c['states'] for c in cases),'original_frozen_experiment_rerun':False,'claim':'finite integer quotient plus explicit witness only'}
    (ROOT/'evidence/LEGACY_AFC_COMPARISON.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'states':result['total_states']}))
if __name__=='__main__':main()
