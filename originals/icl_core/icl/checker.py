"""Nominal primitive + structural compound types and conservative effect analysis."""
import math,re
from .runtime import ICLError,BUILTINS
BASIC={'Int64','Float64','Bool','String','Observer','Context','ProvenanceRef','RecoveryWitness','Capability'}
def split_types(s):
    out=[];start=0;d=0
    for i,c in enumerate(s):
        if c in '[{':d+=1
        elif c in ']}':d-=1
        elif c==',' and d==0:out.append(s[start:i]);start=i+1
    out.append(s[start:]);return out

def valid_type(t):
    if t in BASIC:return True
    if t.startswith('Tensor['):
        try:d=[int(x) for x in t[7:-1].split(',')];return t.endswith(']') and 1<=len(d)<=3 and all(x>0 for x in d) and math.prod(d)<=4096
        except ValueError:return False
    for g in ('List','Option','Result','Representation','Exact','Approx','Tuple'):
        if t.startswith(g+'[') and t.endswith(']'):
            ts=split_types(t[len(g)+1:-1]);return len(ts)>=1 and all(valid_type(x) for x in ts) and (g=='Tuple' or len(ts)==1)
    return False

def shape(t):
    if not t.startswith('Tensor['):raise ICLError('TYPE','Tensor required')
    return [int(x) for x in t[7:-1].split(',')]
def tt(s):return 'Tensor['+','.join(map(str,s))+']'

def check(program):
    fs={};effects=set();ops=[];shapes=[]
    for f in program['functions']:
        if f['name'] in fs or f['name'] in BUILTINS:raise ICLError('NAME','duplicate/reserved function '+f['name'],f.get('span'))
        if not valid_type(f['return_type']):raise ICLError('TYPE','unsupported return type '+f['return_type'])
        if len({n for n,t in f['params']})!=len(f['params']):raise ICLError('NAME','duplicate parameter')
        for n,t in f['params']:
            if not valid_type(t):raise ICLError('TYPE','unsupported parameter type '+t)
        fs[f['name']]=f
    def same(a,b,span=None):
        if a!=b:raise ICLError('TYPE',f'{a} incompatible with {b}',span)
    def ex(x,env):
        k=x['kind'];sp=x.get('span')
        if k=='literal':
            v=x['value'];t='Bool' if type(v)==bool else 'Int64' if type(v)==int else 'Float64' if type(v)==float else 'String'
            if type(v)==int and not -(1<<63)<=v<(1<<63):raise ICLError('OVERFLOW','literal outside Int64',sp)
            if type(v)==float and not math.isfinite(v):raise ICLError('NONFINITE','nonfinite literal',sp)
        elif k=='var':
            if x['name'] not in env:raise ICLError('NAME','undefined name '+x['name'],sp)
            t=env[x['name']][0]
        elif k=='unary':
            # Smallest Int64 is expressed by unary minus of its magnitude.
            if x['op']=='-' and x['expr']['kind']=='literal' and type(x['expr']['value'])==int and x['expr']['value']==(1<<63):
                x['expr']['inferred_type']='Int64';t='Int64'
            else:
                a=ex(x['expr'],env);t='Bool' if x['op']=='!' else a
                if x['op']=='!':same(a,'Bool',sp)
                elif a not in ('Int64','Float64'):raise ICLError('TYPE','numeric negation only',sp)
        elif k=='binary':
            a=ex(x['left'],env);b=ex(x['right'],env);same(a,b,sp);op=x['op']
            if op in ('&&','||'):same(a,'Bool',sp);t='Bool'
            elif op in ('==','!='):t='Bool'
            elif op in ('<','<=','>','>='):
                if a not in ('Int64','Float64','String'):raise ICLError('TYPE','ordered scalar required',sp)
                t='Bool'
            else:
                if a not in ('Int64','Float64') and not(op=='+' and a=='String'):raise ICLError('TYPE','numeric arithmetic only',sp)
                t=a
        elif k in ('list','tuple'):
            ts=[ex(y,env) for y in x['items']]
            if not ts:raise ICLError('TYPE','empty literal needs unsupported explicit type; use nonempty literals',sp)
            if k=='list':
                for a in ts:same(a,ts[0],sp)
                t='List['+ts[0]+']'
            else:t='Tuple['+','.join(ts)+']'
        elif k=='record':t='Record{'+','.join(n+':'+ex(v,env) for n,v in sorted(x['fields'].items()))+'}'
        elif k=='field':
            a=ex(x['target'],env)
            if not a.startswith('Record{'):raise ICLError('TYPE','record required',sp)
            fields=dict(item.split(':',1) for item in split_types(a[7:-1]))
            if x['name'] not in fields:raise ICLError('NAME','no such record field',sp)
            t=fields[x['name']]
        elif k=='index':
            a=ex(x['target'],env);same(ex(x['index'],env),'Int64',sp)
            if a.startswith('List['):t=a[5:-1]
            elif a=='String':t='String'
            elif a.startswith('Tuple['):
                ix=x['index']
                if ix['kind']!='literal' or type(ix['value'])!=int:raise ICLError('TYPE','tuple index must be literal',sp)
                ts=split_types(a[6:-1]);i=ix['value']
                if i<0 or i>=len(ts):raise ICLError('INDEX','tuple index out of range',sp)
                t=ts[i]
            else:raise ICLError('TYPE','indexable value required',sp)
        elif k=='call':
            nm=x['name'];args=x['args'];ts=[ex(y,env) for y in args]
            def sig(types,ret):
                if len(ts)!=len(types):raise ICLError('TYPE',nm+' arity mismatch',sp)
                for a,b in zip(ts,types):same(a,b,sp)
                return ret
            def ar(n):
                if len(ts)!=n:raise ICLError('TYPE',nm+' arity mismatch',sp)
            if nm in fs:t=sig([v for n,v in fs[nm]['params']],fs[nm]['return_type'])
            elif nm=='len':
                ar(1)
                if ts[0]!='String' and not ts[0].startswith('List['):raise ICLError('TYPE','len list/string',sp)
                t='Int64'
            elif nm in ('abs','min','max'):
                ar(1 if nm=='abs' else 2)
                if ts[0] not in ('Int64','Float64') or len(set(ts))!=1:raise ICLError('TYPE','numeric homogeneous inputs')
                t=ts[0]
            elif nm=='to_float':t=sig(['Int64'],'Float64')
            elif nm=='tensor':
                sig(['List[Float64]','List[Int64]'],'')
                sh=args[1]
                if sh['kind']!='list' or any(y['kind']!='literal' or type(y['value'])!=int for y in sh['items']):raise ICLError('SHAPE','tensor shape must be literal',sp)
                ds=[y['value'] for y in sh['items']];t=tt(ds)
                if not valid_type(t):raise ICLError('SHAPE','invalid tensor shape',sp)
                if args[0]['kind']=='list' and len(args[0]['items'])!=math.prod(ds):raise ICLError('SHAPE','tensor literal data length',sp)
                shapes.append({'op':'tensor','shape':ds})
            elif nm=='matmul':
                ar(2);a=shape(ts[0]);b=shape(ts[1])
                if len(a)!=2 or len(b)!=2 or a[1]!=b[0]:raise ICLError('SHAPE','matmul dimensions',sp)
                t=tt([a[0],b[1]]);shapes.append({'op':'matmul','left':a,'right':b,'output':[a[0],b[1]]})
            elif nm in ('add','sub','mul'):
                ar(2);shape(ts[0]);same(ts[0],ts[1],sp);t=ts[0]
            elif nm in ('relu','tanh','normalize','softmax','sum'):
                ar(1);shape(ts[0]);t='Float64' if nm=='sum' else ts[0]
            elif nm=='reshape':
                ar(2);a=shape(ts[0]);same(ts[1],'List[Int64]')
                if args[1]['kind']!='list' or any(y['kind']!='literal' or type(y['value'])!=int for y in args[1]['items']):raise ICLError('SHAPE','reshape literal shape required')
                b=[y['value'] for y in args[1]['items']];t=tt(b)
                if not valid_type(t) or math.prod(a)!=math.prod(b):raise ICLError('SHAPE','reshape elements differ')
            elif nm in ('some','ok'):ar(1);t=('Option' if nm=='some' else 'Result')+'['+ts[0]+']'
            elif nm=='none_int':t=sig([],'Option[Int64]')
            elif nm=='err_int':t=sig(['String'],'Result[Int64]')
            elif nm in ('unwrap','is_some'):
                ar(1)
                if not ts[0].startswith(('Option[','Result[')):raise ICLError('TYPE','Option/Result required')
                if nm=='is_some' and not ts[0].startswith('Option['):raise ICLError('TYPE','Option required')
                t='Bool' if nm=='is_some' else ts[0][ts[0].index('[')+1:-1]
            elif nm=='observer':t=sig(['String'],'Observer')
            elif nm=='context':t=sig(['String','String'],'Context')
            elif nm=='provenance':t=sig(['String'],'ProvenanceRef')
            elif nm=='represent':ar(4);sig([ts[0],'String','String','String'],'');t='Representation['+ts[0]+']'
            elif nm=='repr_value':
                ar(1)
                if not ts[0].startswith('Representation['):raise ICLError('TYPE','Representation required')
                t=ts[0][15:-1]
            elif nm=='repr_add':
                ar(2);same(ts[0],ts[1])
                if ts[0] not in ('Representation[Int64]','Representation[Float64]'):raise ICLError('TYPE','numeric representations required')
                t=ts[0]
            elif nm=='convert_frame':
                ar(4)
                if ts[0] not in ('Representation[Int64]','Representation[Float64]'):raise ICLError('TYPE','numeric representation required')
                t=sig([ts[0],'String',ts[0][15:-1],'String'],ts[0])
            elif nm=='observe_mod':t=sig(['Int64','Int64','String'],'Representation[Int64]')
            elif nm=='make_witness':t=sig(['Int64','Int64'],'RecoveryWitness')
            elif nm=='recover':t=sig(['Representation[Int64]','RecoveryWitness'],'Exact[Int64]')
            elif nm=='recover_without_witness':t=sig(['Representation[Int64]'],'Exact[Int64]')
            elif nm=='exact_value':
                ar(1)
                if not ts[0].startswith('Exact['):raise ICLError('TYPE','Exact required')
                t=ts[0][6:-1]
            elif nm=='approx':t=sig(['Float64','Float64'],'Approx[Float64]')
            elif nm=='approx_value':t=sig(['Approx[Float64]'],'Float64')
            elif nm=='request_effect':t=sig(['String','String'],'Bool');effects.add('policy_request')
            elif nm=='random_int':t=sig(['Int64'],'Int64');effects.add('prng')
            else:raise ICLError('NAME','unknown function '+nm,sp)
            ops.append({'name':nm,'operand_types':ts,'result_type':t})
        else:raise ICLError('UNSUPPORTED_OP',k,sp)
        x['inferred_type']=t;return t
    def body(ss,outer,ret):
        env=dict(outer);local=set();always=False
        for s in ss:
            k=s['kind'];sp=s.get('span')
            if k=='let':
                if s['name'] in local:raise ICLError('NAME','duplicate local binding',sp)
                t=ex(s['expr'],env)
                if s.get('type'):
                    if not valid_type(s['type']):raise ICLError('TYPE','invalid local type',sp)
                    same(t,s['type'],sp)
                env[s['name']]=(t,s['mutable']);local.add(s['name']);s['inferred_type']=t
            elif k=='assign':
                if s['name'] not in env:raise ICLError('NAME','undefined assignment',sp)
                t,mut=env[s['name']]
                if not mut:raise ICLError('IMMUTABLE','cannot assign let/parameter',sp)
                same(ex(s['expr'],env),t,sp)
            elif k=='return':same(ex(s['expr'],env),ret,sp);always=True
            elif k=='expr':ex(s['expr'],env)
            elif k=='if':
                same(ex(s['cond'],env),'Bool',sp);a=body(s['then'],env,ret);b=body(s['else'],env,ret);always=always or (a and b)
            elif k=='while':same(ex(s['cond'],env),'Bool',sp);body(s['body'],env,ret)
            else:raise ICLError('UNSUPPORTED_OP',k,sp)
        return always
    for f in program['functions']:
        env={n:(t,False) for n,t in f['params']}
        if not body(f['body'],env,f['return_type']):raise ICLError('RETURN','function must return on every path',f.get('span'))
    return {'program':program,'effects':sorted(effects),'ops':ops,'shape_constraints':shapes}

def validate_value(value,t,ctx):
    ctx.check_value(value)
    valid=False
    if t=='Int64':valid=type(value)==int
    elif t=='Float64':valid=type(value)==float
    elif t=='Bool':valid=type(value)==bool
    elif t=='String':valid=type(value)==str
    elif t.startswith('Tensor['):
        from .runtime import validate_tensor
        v=validate_tensor(value,ctx);valid=v['shape']==shape(t)
    elif t.startswith('List['):valid=type(value)==list and all(validate_value(x,t[5:-1],ctx) for x in value)
    elif t.startswith('Tuple['):
        ts=split_types(t[6:-1]);valid=type(value)==list and len(value)==len(ts) and all(validate_value(x,st,ctx) for x,st in zip(value,ts))
    elif t.startswith('Record{'):
        fields=dict(item.split(':',1) for item in split_types(t[7:-1]));valid=isinstance(value,dict) and set(value)==set(fields) and all(validate_value(value[k],st,ctx) for k,st in fields.items())
    elif isinstance(value,dict):
        tag=t.split('[',1)[0];inner=t[t.index('[')+1:-1] if '[' in t else None
        def fields(required):return all(k in value for k in required)
        if tag=='Option':
            valid=value.get('tag')=='None' and value.get('value') is None
            if value.get('tag')=='Some':valid=fields(['value']) and validate_value(value['value'],inner,ctx)
        elif tag=='Result':
            valid=value.get('tag')=='Err' and isinstance(value.get('error'),str)
            if value.get('tag')=='Ok':valid=fields(['value']) and validate_value(value['value'],inner,ctx)
        elif tag=='Representation':
            valid=value.get('tag')==tag and fields(['value','observer','frame','unit','source_hash','provenance']) and all(isinstance(value[k],str) for k in ('observer','frame','unit')) and isinstance(value['provenance'],dict) and (value['source_hash'] is None or isinstance(value['source_hash'],str))
            if valid:valid=validate_value(value['value'],inner,ctx)
            if 'modulus' in value:valid=valid and type(value['modulus'])==int and value['modulus']>0
        elif tag=='Exact':
            valid=value.get('tag')==tag and fields(['value','witness_bytes','scope']) and type(value['witness_bytes'])==int and value['witness_bytes']>=0 and isinstance(value['scope'],str)
            if valid:valid=validate_value(value['value'],inner,ctx)
        elif tag=='Approx':
            valid=value.get('tag')==tag and fields(['value','error_bound']) and type(value['error_bound'])==float and value['error_bound']>=0
            if valid:valid=validate_value(value['value'],inner,ctx)
        elif tag=='Observer':valid=value.get('tag')==tag and isinstance(value.get('id'),str)
        elif tag=='Context':valid=value.get('tag')==tag and isinstance(value.get('frame'),str) and isinstance(value.get('unit'),str)
        elif tag=='ProvenanceRef':valid=value.get('tag')==tag and isinstance(value.get('source_id'),str) and value.get('verified') is False
        elif tag=='RecoveryWitness':
            valid=value.get('tag')==tag and all(type(value.get(k))==int for k in ('quotient','modulus','remainder','payload_bytes')) and value.get('modulus',0)>0 and value.get('payload_bytes',-1)>=0 and isinstance(value.get('sha256'),str)
        elif tag=='Capability':valid=False  # no transferable authority values in v0.1
    if not valid:raise ICLError('TYPE','input does not match '+t)
    return True
