#!/usr/bin/env python3
"""Offline ICL-Core acceptance runner. Emits complete evidence, never synthesizes PASS."""
from __future__ import annotations
import collections, hashlib, json, math, os, pathlib, sys, time, traceback
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from cases import CASES,Case
from generated_cases import generate,SEED
from adversarial_cases import ADVERSARIAL
from graph_cases import graph_cases

ATOL=1e-10
RTOL=1e-10

def plain(x):
    if hasattr(x,'tolist'):return plain(x.tolist())
    if hasattr(x,'to_dict'):return plain(x.to_dict())
    if hasattr(x,'__dict__'):return {k:plain(v) for k,v in vars(x).items()}
    if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    return x

def equal(a,b):
    a,b=plain(a),plain(b)
    if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,(float,int)) and not isinstance(a,bool) and isinstance(b,(float,int)) and not isinstance(b,bool):
        if isinstance(a,int) and isinstance(b,int):return a==b
        return math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,abs_tol=ATOL,rel_tol=RTOL)
    return type(a)==type(b) and a==b

def error_record(exc):
    return {'code':str(getattr(exc,'code',type(exc).__name__)),'message':str(exc),'span':plain(getattr(exc,'span',None))}

def execute_case(case, index, generated=False):
    from icl.api import compile_source,run_source
    from icl.frontend import parse,pretty,canonical_ast
    rec={'id':case.name,'index':index,'family':case.family,'source':case.source,'source_sha256':hashlib.sha256(case.source.encode()).hexdigest(),'arguments':case.args,'expected':plain(case.expected),'expected_error':case.error,'seed':SEED if generated else None}
    engines={}
    for eng in ('tree','vm'):
        try:
            result=run_source(case.source,args=case.args,engine=eng,module_map=case.modules,limits=case.limits,policy=case.policy)
            engines[eng]={'value':plain(result['value']),'effects':plain(result.get('effects',[])),'steps':result.get('steps'),'trace_events':len(result.get('trace',[]))}
        except Exception as e:engines[eng]={'error':error_record(e)}
    rec['engines']=engines
    if case.error:
        rec['passed']=all(v.get('error',{}).get('code')==case.error for v in engines.values())
    else:
        rec['passed']=all('error' not in v and equal(v.get('value'),case.expected) for v in engines.values()) and equal(engines['vm'].get('effects'),engines['tree'].get('effects'))
    try:
        ast=parse(case.source);again=parse(pretty(ast));rec['ast_roundtrip']=canonical_ast(ast)==canonical_ast(again)
        if not case.error:rec['passed']=rec['passed'] and rec['ast_roundtrip']
    except Exception as e:
        rec['ast_roundtrip_error']=error_record(e)
        if not case.error:rec['passed']=False
    return rec

def summary(records):
    return {'total':len(records),'passed':sum(bool(r['passed']) for r in records),'failed':sum(not r['passed'] for r in records),'families':dict(collections.Counter(r['family'] for r in records)),'failures':[r['id'] for r in records if not r['passed']]}

def write_json(path,obj):path.write_text(json.dumps(plain(obj),ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def main():
    started=time.time();out=ROOT/'evidence';out.mkdir(exist_ok=True)
    def sources_snapshot():return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ('icl','tests') for p in sorted((ROOT/base).rglob('*.py'))}
    before=sources_snapshot()
    records=[]
    for i,c in enumerate(CASES):
        sub='invalid' if c.error else 'valid';(ROOT/'tests/programs'/sub).mkdir(parents=True,exist_ok=True)
        (ROOT/'tests/programs'/sub/(c.name+'.icl')).write_text(c.source+'\n')
        records.append(execute_case(c,i))
    write_json(out/'HANDWRITTEN_RESULTS.json',records)
    gen=[]
    with (out/'DIFFERENTIAL_CASES.jsonl').open('w') as f:
        for i,c in enumerate(generate()):
            r=execute_case(c,i,True);gen.append(r);f.write(json.dumps(plain(r),ensure_ascii=False,allow_nan=False)+'\n')
    adversarial=[execute_case(c,i) for i,c in enumerate(ADVERSARIAL)]
    for c in ADVERSARIAL:
        (ROOT/'tests/programs/invalid'/(c.name+'.icl')).write_text(c.source+'\n')
    write_json(out/'ADVERSARIAL_RESULTS.json',adversarial)
    graphs=[execute_case(c,i) for i,c in enumerate(graph_cases())]
    write_json(out/'NUMPY_GRAPH_PARITY.json',graphs)
    from contract_cases import run_contracts
    contracts=run_contracts()
    write_json(out/'CONTRACT_RESULTS.json',contracts)
    from cli_cases import run_cli_cases
    cli=run_cli_cases()
    write_json(out/'CLI_RESULTS.json',cli)
    result={'status':'PASS' if all(r['passed'] for r in records+gen+adversarial+graphs+contracts+cli) else 'FAIL','test_protocol':'ICL_ACCEPTANCE_v0.1','tolerance_fixed_before_run':{'atol':ATOL,'rtol':RTOL},'seed':SEED,'handwritten':summary(records),'generated':summary(gen),'adversarial':summary(adversarial),'numpy_graphs':summary(graphs),'contracts':summary(contracts),'cli':summary(cli),'elapsed_seconds':time.time()-started,'execution_engines':'independent tree control flow and bytecode VM; shared scalar/builtin primitives are documented'}
    after=sources_snapshot()
    result['source_changed_during_run']=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
    result['unique_generated_source_argument_cases']=len(set((r['source_sha256'],json.dumps(r['arguments'],sort_keys=True)) for r in gen))
    if result['source_changed_during_run']:result['status']='FAIL'
    import platform,datetime,numpy
    write_json(out/'TEST_ENVIRONMENT.json',{'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'numpy':numpy.__version__,'test_run':'acceptance_stdout.log','implementation_and_test_sha256':before,'source_stable':not result['source_changed_during_run']})
    write_json(out/'TEST_RESULTS.json',result);print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
