"""Public compile/check/run/serialize contract. Never resolves filesystem imports."""
import copy,hashlib,json,re
from pathlib import Path
from .frontend import parse,canonical_ast,pretty
from .checker import check,validate_value
from .runtime import ICLError,RuntimeContext,canonical,digest,DEFAULT_LIMITS
from .interpreter import execute_tree
from .vm import compile_bytecode,execute_bytecode
SCHEMA_VERSION='0.1.0'
SCHEMA_PATH=Path(__file__).with_name('OCIR_SCHEMA.json')
if not SCHEMA_PATH.exists():SCHEMA_PATH=Path(__file__).parent.parent/'OCIR_SCHEMA.json'
SCHEMA_SHA256=hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()
FEATURES=['functions','modules','lexical_scope','checked_int64','finite_float64','bounded_loop','list','record','tuple','option','result','tensor','observer','recovery','policy_effect','checkpoint']
NUMERIC={'int64':'checked_signed','integer_division':'truncate_toward_zero','float64':'finite_only','atol':1e-6,'rtol':1e-5,'normalize_epsilon':1e-5}

def load_program(source,module_map=None):
    modules=module_map or {}
    if not isinstance(modules,dict) or len(modules)>64:raise ICLError('IMPORT','module map must have <=64 entries')
    visiting=set();done={};graph=[];functions=[]
    root=parse(source)
    def visit(p,src,isroot=False):
        nm=p['module']
        if nm in visiting:raise ICLError('IMPORT_CYCLE','cyclic module import')
        if nm in done:return
        visiting.add(nm)
        if len(visiting)>32:raise ICLError('IMPORT_LIMIT','import nesting limit')
        for name in p['imports']:
            if name not in modules:raise ICLError('IMPORT','missing explicit module '+name)
            sub=parse(modules[name])
            if sub['module']!=name:raise ICLError('IMPORT','module declaration mismatch')
            visit(sub,modules[name])
        own={f['name'] for f in p['functions']}
        def rename(v):
            if isinstance(v,dict):
                if v.get('kind')=='call':
                    target=v['name']
                    if target in own and not isroot:v['name']=nm+'.'+target
                    elif '.' in target and target.split('.')[0] not in p['imports']:raise ICLError('IMPORT','qualified call without import')
                for child in v.values():rename(child)
            elif isinstance(v,list):
                for child in v:rename(child)
        rename(p)
        for f in p['functions']:
            if not isroot:f['name']=nm+'.'+f['name']
            functions.append(f)
        graph.append({'module':nm,'imports':p['imports'],'source_sha256':hashlib.sha256(src.encode()).hexdigest()})
        visiting.remove(nm);done[nm]=True
    visit(root,source,True)
    return {'module':root['module'],'imports':root['imports'],'functions':functions},graph

def compile_source(source,module_map=None,limits=None,entry='main'):
    p,graph=load_program(source,module_map);c=check(p);ctx=RuntimeContext(limits)
    if entry not in {f['name'] for f in p['functions']}:raise ICLError('NAME','entrypoint missing')
    source_hash=hashlib.sha256(source.encode()).hexdigest()
    ocir={'schema_version':SCHEMA_VERSION,'schema_sha256':SCHEMA_SHA256,'feature_set':list(FEATURES),'program_id':digest({'ast':canonical_ast(p),'modules':graph}),'source_sha256':source_hash,'module_graph':graph,'typed_blocks':p['functions'],'ops':c['ops'],'operand_types':[o['operand_types'] for o in c['ops']],'shape_constraints':c['shape_constraints'],'observer_context':{'mode':'explicit_metadata','implicit_conversion':False},'provenance_refs':[{'source_sha256':g['source_sha256'],'module':g['module'],'status':'COMPILED_LOCAL_SOURCE'} for g in graph],'required_effects':c['effects'],'limits':ctx.limits,'numeric_policy':dict(NUMERIC),'entrypoint':entry}
    ocir['integrity_sha256']=digest(ocir);return ocir

def check_source(source,**kwargs):return compile_source(source,**kwargs)
def canonicalize_source(source):return canonical_ast(parse(source))
def pretty_source(source):return pretty(parse(source))

AST_KEYS={
'literal':{'kind','value'},'var':{'kind','name'},'binary':{'kind','op','left','right'},'unary':{'kind','op','expr'},'call':{'kind','name','args'},'list':{'kind','items'},'tuple':{'kind','items'},'record':{'kind','fields'},'index':{'kind','target','index'},'field':{'kind','target','name'},'let':{'kind','name','type','mutable','expr'},'assign':{'kind','name','expr'},'return':{'kind','expr'},'expr':{'kind','expr'},'if':{'kind','cond','then','else'},'while':{'kind','cond','limit','body'}}
def validate_ocir(ocir):
    if not isinstance(ocir,dict):raise ICLError('OCIR_CORRUPT','object required')
    try:
        if ocir.get('schema_version')!=SCHEMA_VERSION or ocir.get('schema_sha256')!=SCHEMA_SHA256:raise ICLError('SCHEMA_INCOMPATIBLE','OCIR schema/hash differs')
        data={k:v for k,v in ocir.items() if k!='integrity_sha256'}
        if digest(data)!=ocir.get('integrity_sha256'):raise ICLError('CHECKSUM','OCIR integrity mismatch')
        required=set(json.loads(SCHEMA_PATH.read_text())['required'])
        if set(ocir)!=required:raise ICLError('OCIR_CORRUPT','unexpected/missing OCIR fields')
        if ocir['numeric_policy']!=NUMERIC or ocir['feature_set']!=FEATURES:raise ICLError('SCHEMA_INCOMPATIBLE','numeric/feature policy differs')
        ctx=RuntimeContext(ocir['limits']);ctx.check_value(ocir)
        count=0
        def walk(v,depth=0):
            nonlocal count
            count+=1
            if count>100000 or depth>128:raise ICLError('OCIR_CORRUPT','AST size/depth limit')
            if isinstance(v,dict):
                if 'kind' in v:
                    k=v['kind']
                    if k not in AST_KEYS:raise ICLError('UNSUPPORTED_OP','unknown AST opcode')
                    if set(v)-{'span','inferred_type'}!=AST_KEYS[k]:raise ICLError('OCIR_CORRUPT','malformed AST operation')
                    if k=='binary' and v['op'] not in ('+','-','*','/','%','==','!=','<','<=','>','>=','&&','||'):raise ICLError('UNSUPPORTED_OP','binary opcode')
                    if k=='unary' and v['op'] not in ('-','!'):raise ICLError('UNSUPPORTED_OP','unary opcode')
                    if k=='while' and (type(v['limit'])!=int or not 0<=v['limit']<=100000):raise ICLError('OCIR_CORRUPT','invalid loop limit')
                for child in v.values():walk(child,depth+1)
            elif isinstance(v,list):
                for child in v:walk(child,depth+1)
        walk(ocir['typed_blocks'])
        p={'module':ocir['module_graph'][-1]['module'],'imports':ocir['module_graph'][-1]['imports'],'functions':copy.deepcopy(ocir['typed_blocks'])};checked=check(p)
        if digest({'ast':canonical_ast(p),'modules':ocir['module_graph']})!=ocir['program_id']:raise ICLError('OCIR_CORRUPT','program identity inconsistent')
        if p['functions']!=ocir['typed_blocks'] or checked['ops']!=ocir['ops'] or checked['effects']!=ocir['required_effects'] or checked['shape_constraints']!=ocir['shape_constraints']:raise ICLError('OCIR_CORRUPT','typed data differs from checker')
        if ocir['operand_types']!=[o['operand_types'] for o in checked['ops']]:raise ICLError('OCIR_CORRUPT','operand types differ')
        if ocir['entrypoint'] not in {f['name'] for f in p['functions']}:raise ICLError('NAME','invalid entrypoint')
        return p
    except ICLError:raise
    except (KeyError,TypeError,ValueError,IndexError,RecursionError,OverflowError) as e:raise ICLError('OCIR_CORRUPT','invalid serialized structure: '+type(e).__name__)

def dumps_ocir(ocir):validate_ocir(ocir);return canonical(ocir)
def loads_ocir(text):
    try:
        if not isinstance(text,str) or len(text.encode())>4000000:raise ICLError('OCIR_CORRUPT','serialized size limit')
    except UnicodeError:raise ICLError('OCIR_CORRUPT','invalid Unicode')
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ICLError('OCIR_CORRUPT','duplicate key')
            d[k]=v
        return d
    try:o=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ICLError('NONFINITE','JSON nonfinite')))
    except (ValueError,RecursionError):raise ICLError('OCIR_CORRUPT','invalid JSON')
    validate_ocir(o);return o

def run_ocir(ocir,args=None,engine='vm',entry=None,policy=None,limits=None,checkpoint=None,stop_after=None):
    p=validate_ocir(ocir);entry=entry or ocir['entrypoint'];args=[] if args is None else args
    requested=RuntimeContext(limits).limits if limits is not None else ocir['limits']
    lim={k:min(requested[k],ocir['limits'][k]) for k in DEFAULT_LIMITS};ctx=RuntimeContext(lim,policy)
    fn=next((f for f in p['functions'] if f['name']==entry),None)
    if fn is None:raise ICLError('NAME','entry missing')
    if not isinstance(args,list) or len(args)!=len(fn['params']):raise ICLError('TYPE','entry argument count')
    for (_,tp),v in zip(fn['params'],args):validate_value(v,tp,ctx)
    if engine=='tree':
        if checkpoint is not None or stop_after is not None:raise ICLError('UNSUPPORTED_OP','tree checkpoint unsupported; VM checkpoint supported')
        return execute_tree(p,entry,args,lim,policy)
    if engine!='vm':raise ICLError('ENGINE','unknown execution engine')
    out=execute_bytecode(compile_bytecode(p),entry,args,lim,policy,checkpoint,stop_after)
    if 'value' in out and out.get('checkpoint') is None:validate_value(out['value'],fn['return_type'],ctx)
    return out

def run_source(source,args=None,engine='vm',entry='main',module_map=None,limits=None,policy=None,checkpoint=None,stop_after=None):
    return run_ocir(compile_source(source,module_map,limits,entry),args,engine,entry,policy,limits,checkpoint,stop_after)
