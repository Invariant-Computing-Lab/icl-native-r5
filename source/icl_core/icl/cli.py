"""Offline CLI. JSON diagnostics on stderr, successful JSON on stdout."""
import argparse,json,sys
from pathlib import Path
from . import __version__
from .api import compile_source,run_source,run_ocir,loads_ocir,dumps_ocir,SCHEMA_SHA256
from .runtime import ICLError,digest

def read(path,max_bytes=4000000):
    p=Path(path)
    if p.is_symlink() or any(parent.is_symlink() for parent in p.parents):raise ICLError('PATH','symlinks are not accepted')
    if not p.is_file():raise ICLError('PATH','regular file required')
    if p.stat().st_size>max_bytes:raise ICLError('SOURCE_LIMIT','file size exceeded')
    try:return p.read_text(encoding='utf-8')
    except (UnicodeError,OSError):raise ICLError('PATH','UTF-8 file unavailable')
def js(text):
    try:return json.loads(text,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
    except (ValueError,RecursionError):raise ICLError('JSON','invalid finite JSON argument')
def output(obj):print(json.dumps(obj,ensure_ascii=False,allow_nan=False,sort_keys=True))
def main(argv=None):
    parser=argparse.ArgumentParser(prog='icl',description='Invariant Cognition Language finite core, offline v0.1')
    parser.add_argument('--version',action='version',version=__version__)
    subs=parser.add_subparsers(dest='command',required=True)
    for name in ('check','run','compile'):
        p=subs.add_parser(name);p.add_argument('source');p.add_argument('--module-map',help='JSON file mapping module names to source text');p.add_argument('--entry',default='main');p.add_argument('--json',action='store_true',help='JSON is also the default output')
        p.add_argument('--max-steps',type=int)
        if name=='run':
            p.add_argument('--args',default='[]',help='JSON argument array');p.add_argument('--engine',choices=['vm','tree'],default='vm');p.add_argument('--policy',help='Separate trusted host policy JSON file');p.add_argument('--trace',action='store_true');p.add_argument('--stop-after',type=int);p.add_argument('--checkpoint-out')
        if name=='compile':p.add_argument('-o','--output',required=True)
    p=subs.add_parser('inspect');p.add_argument('ocir');p.add_argument('--json',action='store_true')
    p=subs.add_parser('replay');p.add_argument('ocir');p.add_argument('checkpoint');p.add_argument('--args',default='[]');p.add_argument('--policy');p.add_argument('--json',action='store_true');p.add_argument('--trace',action='store_true')
    p=subs.add_parser('test');p.add_argument('--json',action='store_true')
    a=parser.parse_args(argv)
    try:
        if a.command in ('check','run','compile'):
            source=read(a.source,1000000);modules=js(read(a.module_map)) if a.module_map else None;limits={'max_steps':a.max_steps} if a.max_steps is not None else None
            ocir=compile_source(source,modules,limits,a.entry)
            if a.command=='check':output({'status':'PASS','schema_sha256':SCHEMA_SHA256,'program_id':ocir['program_id'],'required_effects':ocir['required_effects']});return 0
            if a.command=='compile':
                Path(a.output).write_text(dumps_ocir(ocir)+'\n',encoding='utf-8');output({'status':'PASS','output':a.output,'sha256':ocir['integrity_sha256']});return 0
            policy=js(read(a.policy)) if a.policy else None
            r=run_ocir(ocir,js(a.args),a.engine,policy=policy,stop_after=a.stop_after)
            if a.checkpoint_out and r.get('checkpoint'):Path(a.checkpoint_out).write_text(json.dumps(r['checkpoint'],sort_keys=True),encoding='utf-8')
        elif a.command=='inspect':
            o=loads_ocir(read(a.ocir));output({'schema_version':o['schema_version'],'schema_sha256':o['schema_sha256'],'program_id':o['program_id'],'entrypoint':o['entrypoint'],'functions':[f['name'] for f in o['typed_blocks']],'required_effects':o['required_effects'],'limits':o['limits'],'integrity':'PASS'});return 0
        elif a.command=='replay':
            o=loads_ocir(read(a.ocir));r=run_ocir(o,js(a.args),policy=js(read(a.policy)) if a.policy else None,checkpoint=js(read(a.checkpoint)))
        else:
            fixtures=[('arithmetic','module t; fn main() -> Int64 { return 7 * 6; }',42),('branch','module t; fn main() -> Int64 { if true { return 1; } else { return 0; } }',1),('function','module t; fn f(x:Int64)->Int64{return x*x;} fn main()->Int64{return f(9);}',81)]
            results=[]
            for name,s,v in fixtures:
                vals=[run_source(s,engine=e)['value'] for e in ('tree','vm')];results.append({'name':name,'passed':vals==[v,v]})
            passed=all(x['passed'] for x in results);output({'status':'PASS' if passed else 'FAIL','tests':results});return 0 if passed else 1
        if not a.trace and 'trace' in r:r['trace_sha256']=digest(r['trace']);r['trace_events']=len(r.pop('trace'))
        output({'status':'PAUSED' if r.get('checkpoint') else 'PASS',**r});return 0
    except ICLError as e:
        print(json.dumps({'status':'ERROR','diagnostic':e.as_dict()},ensure_ascii=False),file=sys.stderr);return 2
    except (OSError,UnicodeError) as e:
        print(json.dumps({'status':'ERROR','diagnostic':{'code':'IO','message':str(e)}}),file=sys.stderr);return 3
if __name__=='__main__':raise SystemExit(main())
