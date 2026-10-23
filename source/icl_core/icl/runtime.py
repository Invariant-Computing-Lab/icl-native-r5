"""Primitive numeric/metadata registry shared by independent execution engines.
No I/O, FFI, shell, eval or dynamic import is exposed by the language.
"""
import hashlib,json,math,operator

class ICLError(Exception):
    def __init__(self,code,message,span=None):
        self.code=code;self.message=message;self.span=span
        super().__init__(f'{code}: {message}')
    def as_dict(self):return {'code':self.code,'message':self.message,'span':self.span}

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
DEFAULT_LIMITS={'max_steps':100000,'max_stack':128,'max_items':100000,'max_output':1000000,'max_tensor':4096}
class RuntimeContext:
    def __init__(self,limits=None,policy=None):
        self.limits=dict(DEFAULT_LIMITS)
        if limits:
            for k,v in limits.items():
                if k not in self.limits or type(v)!=int or v<1 or v>DEFAULT_LIMITS[k]:raise ICLError('RESOURCE_POLICY','limits may only reduce defaults')
                self.limits[k]=v
        self.policy={} if policy is None else policy
        if not isinstance(self.policy,dict):raise ICLError('RESOURCE_POLICY','policy must be object')
        for action,permission in self.policy.items():
            if not isinstance(action,str) or not isinstance(permission,dict) or set(permission)-{'allow','human_required','human_approved'}:raise ICLError('RESOURCE_POLICY','invalid policy descriptor')
            if any(type(v)!=bool for v in permission.values()):raise ICLError('RESOURCE_POLICY','policy flags require strict booleans')
        self.steps=0;self.trace=[];self.effects=[];self.prng=1
    def step(self,op='',inputs=None,output=None):
        self.steps+=1
        if self.steps>self.limits['max_steps']:raise ICLError('FUEL_EXHAUSTED','step budget exceeded')
        self.trace.append({'run_id':'deterministic','step':self.steps,'op_id':op,'input_hash':digest(inputs),'output_hash':digest(output),'state_ref':None,'effect_request':None,'effect_decision':None,'recovery_ref':None,'error_code':None,'clock_mode':'logical'})
    def check_value(self,value):
        count=0
        def walk(v,depth=0):
            nonlocal count
            count+=1
            if depth>128 or count>self.limits['max_items']:raise ICLError('MEMORY_LIMIT','value size/depth limit')
            if isinstance(v,(list,tuple)):
                for x in v:walk(x,depth+1)
            elif isinstance(v,dict):
                for x in v.values():walk(x,depth+1)
            elif isinstance(v,float) and not math.isfinite(v):raise ICLError('NONFINITE','NaN/Inf forbidden')
            elif type(v)==int and not -(1<<63)<=v<(1<<63):raise ICLError('OVERFLOW','Int64 overflow')
            elif isinstance(v,str) and len(v.encode())>self.limits['max_output']:raise ICLError('OUTPUT_LIMIT','string too large')
        walk(value)
        if len(canonical(value).encode())>self.limits['max_output']:raise ICLError('OUTPUT_LIMIT','serialized value too large')
        return value

def checked_num(v):
    if type(v)==int and not -(1<<63)<=v<(1<<63):raise ICLError('OVERFLOW','Int64 overflow')
    if isinstance(v,float) and not math.isfinite(v):raise ICLError('NONFINITE','NaN/Inf forbidden')
    return v

def checked_binary(op,a,b):
    if op in ('&&','||'):
        if type(a)!=bool or type(b)!=bool:raise ICLError('TYPE','Bool operands required')
        return a and b if op=='&&' else a or b
    if op in ('==','!='):
        if type(a)!=type(b):raise ICLError('TYPE','same types required')
        return a==b if op=='==' else a!=b
    if op in ('<','<=','>','>='):
        if type(a) not in (int,float,str) or type(a)!=type(b):raise ICLError('TYPE','homogeneous ordered scalar operands required')
        return {'<':operator.lt,'<=':operator.le,'>':operator.gt,'>=':operator.ge}[op](a,b)
    if op=='+' and type(a)==type(b)==str:return a+b
    if type(a) not in (int,float) or type(a)!=type(b):raise ICLError('TYPE','homogeneous numeric operands required')
    if op in ('/','%') and b==0:raise ICLError('DIVISION_BY_ZERO','zero divisor')
    if op=='+':v=a+b
    elif op=='-':v=a-b
    elif op=='*':v=a*b
    elif op=='/':v=(abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1) if type(a)==int else a/b
    elif op=='%':v=a-((abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1))*b if type(a)==int else math.fmod(a,b)
    else:raise ICLError('UNSUPPORTED_OP',op)
    return checked_num(v)
def checked_unary(op,a):
    if op=='!' and type(a)==bool:return not a
    if op=='-' and type(a) in (int,float):return checked_num(-a)
    raise ICLError('TYPE','invalid unary operand')

def tensor(data,shape,ctx):
    if not isinstance(shape,list) or not 1<=len(shape)<=3 or any(type(x)!=int or x<1 for x in shape):raise ICLError('SHAPE','rank 1..3, positive dimensions required')
    n=math.prod(shape)
    if n>ctx.limits['max_tensor']:raise ICLError('TENSOR_LIMIT','tensor element limit')
    if not isinstance(data,list) or n!=len(data):raise ICLError('SHAPE','data length mismatch')
    if any(type(x)!=float or not math.isfinite(x) for x in data):raise ICLError('TYPE','finite Float64 tensor data required')
    return {'shape':shape[:],'data':data[:]}
def istensor(x):return isinstance(x,dict) and set(x)=={'shape','data'}
def validate_tensor(x,ctx):
    if not istensor(x):raise ICLError('TYPE','Tensor required')
    return tensor(x['data'],x['shape'],ctx)

def _builtin(name,args,ctx):
    def n(count):
        if len(args)!=count:raise ICLError('TYPE',f'{name} expects {count} arguments')
    if name=='len':n(1);return len(args[0])
    if name=='abs':n(1);return checked_num(abs(args[0]))
    if name in ('min','max'):n(2);return min(args) if name=='min' else max(args)
    if name=='to_float':n(1);return float(args[0])
    if name=='tensor':n(2);return tensor(args[0],args[1],ctx)
    if name in ('matmul','add','sub','mul'):
        n(2);a,b=[validate_tensor(x,ctx) for x in args]
        if name=='matmul':
            if len(a['shape'])!=2 or len(b['shape'])!=2 or a['shape'][1]!=b['shape'][0]:raise ICLError('SHAPE','matmul dimensions')
            m,k=a['shape'];_,p=b['shape']
            if m*p>ctx.limits['max_tensor']:raise ICLError('TENSOR_LIMIT','matmul output exceeds tensor limit before allocation')
            return tensor([float(sum(a['data'][i*k+t]*b['data'][t*p+j] for t in range(k))) for i in range(m) for j in range(p)],[m,p],ctx)
        if a['shape']!=b['shape']:raise ICLError('SHAPE','elementwise shapes differ')
        op={'add':operator.add,'sub':operator.sub,'mul':operator.mul}[name]
        return tensor([op(x,y) for x,y in zip(a['data'],b['data'])],a['shape'],ctx)
    if name in ('relu','tanh','normalize','softmax'):
        n(1);a=validate_tensor(args[0],ctx);d=a['data'];w=a['shape'][-1]
        if name=='relu':d=[max(0.0,x) for x in d]
        elif name=='tanh':d=[math.tanh(x) for x in d]
        else:
            out=[]
            for j in range(0,len(d),w):
                r=d[j:j+w]
                if name=='softmax':z=[math.exp(x-max(r)) for x in r];s=sum(z);out.extend(x/s for x in z)
                else:
                    mean=checked_num(sum(r)/w)
                    var=checked_num(sum((x-mean)**2 for x in r)/w)
                    out.extend((x-mean)/math.sqrt(var+1e-5) for x in r)
            d=out
        return tensor(d,a['shape'],ctx)
    if name=='reshape':n(2);a=validate_tensor(args[0],ctx);return tensor(a['data'],args[1],ctx)
    if name=='sum':n(1);a=validate_tensor(args[0],ctx);return checked_num(float(sum(a['data'])))
    if name=='some':n(1);return {'tag':'Some','value':args[0]}
    if name=='none_int':n(0);return {'tag':'None','value':None}
    if name=='ok':n(1);return {'tag':'Ok','value':args[0]}
    if name=='err_int':n(1);return {'tag':'Err','error':args[0]}
    if name=='unwrap':
        n(1);a=args[0]
        if a.get('tag') not in ('Some','Ok'):raise ICLError('UNWRAP','empty/Err cannot unwrap')
        return a['value']
    if name=='is_some':n(1);return args[0]['tag']=='Some'
    if name=='observer':n(1);return {'tag':'Observer','id':args[0]}
    if name=='context':n(2);return {'tag':'Context','frame':args[0],'unit':args[1]}
    if name=='provenance':n(1);return {'tag':'ProvenanceRef','source_id':args[0],'verified':False}
    if name=='represent':
        n(4);v,o,f,u=args
        return {'tag':'Representation','value':v,'observer':o,'frame':f,'unit':u,'source_hash':digest(v),'provenance':{'status':'LOCAL_COMPUTATION','claim':'hash_is_integrity_only'}}
    if name=='repr_value':n(1);return args[0]['value']
    if name=='repr_add':
        n(2);a,b=args
        for field,code in [('observer','OBSERVER_MISMATCH'),('frame','FRAME_MISMATCH'),('unit','UNIT_MISMATCH')]:
            if a[field]!=b[field]:raise ICLError(code,field+' mismatch; explicit conversion required')
        return builtin('represent',[checked_binary('+',a['value'],b['value']),a['observer'],a['frame'],a['unit']],ctx)
    if name=='convert_frame':
        n(4);r,new,offset,protocol=args
        if protocol!='affine_translation_v1':raise ICLError('NEEDS_EVIDENCE','unregistered transform protocol')
        out=builtin('represent',[checked_binary('+',r['value'],offset),r['observer'],new,r['unit']],ctx)
        out['provenance']={'source_hash':digest(r),'protocol':protocol,'offset':offset};return out
    if name=='observe_mod':
        n(3);x,m,o=args
        if m<=0:raise ICLError('DOMAIN','positive modulus required')
        r=builtin('represent',[x%m,o,'scalar','dimensionless'],ctx);r['modulus']=m;r['source_hash']=None;r['ambiguous']=True;return r
    if name=='make_witness':
        n(2);x,m=args
        if m<=0:raise ICLError('DOMAIN','positive modulus required')
        payload={'tag':'RecoveryWitness','quotient':x//m,'modulus':m,'remainder':x%m};payload['sha256']=digest(payload);payload['payload_bytes']=len(canonical(payload).encode());return payload
    if name=='recover':
        n(2);r,w=args
        if w.get('tag')!='RecoveryWitness':raise ICLError('WITNESS_MISSING','witness required')
        p={k:w[k] for k in ('tag','quotient','modulus','remainder')}
        if digest(p)!=w.get('sha256'):raise ICLError('WITNESS_CORRUPT','witness checksum')
        if r.get('modulus')!=w['modulus'] or r['value']!=w['remainder']:raise ICLError('WITNESS_CORRUPT','witness measurement mismatch')
        return {'tag':'Exact','value':checked_num(w['quotient']*w['modulus']+w['remainder']),'witness_bytes':w['payload_bytes'],'scope':'declared_integer_modulo_protocol'}
    if name=='recover_without_witness':n(1);raise ICLError('NON_IDENTIFIABLE','measurement has multiple compatible sources')
    if name=='exact_value':n(1);return args[0]['value']
    if name=='approx':
        n(2)
        if args[1]<0:raise ICLError('DOMAIN','nonnegative error bound required')
        return {'tag':'Approx','value':args[0],'error_bound':args[1]}
    if name=='approx_value':n(1);return args[0]['value']
    if name=='request_effect':
        n(2);action,payload=args;permission=ctx.policy.get(action,{})
        allowed=action=='journal' and permission.get('allow') is True
        if permission.get('human_required') is True and permission.get('human_approved') is not True:allowed=False;code='HUMAN_APPROVAL_REQUIRED'
        else:code='EFFECT_DENIED'
        event={'action':action,'payload_hash':digest(payload),'decision':'ALLOWED_LOCAL_JOURNAL' if allowed else 'DENIED','external_executed':False}
        ctx.effects.append(event)
        if not allowed:raise ICLError(code,'trusted host policy denied action')
        return True
    if name=='random_int':
        n(1)
        if args[0]<=0:raise ICLError('DOMAIN','positive PRNG range')
        ctx.prng=(1103515245*ctx.prng+12345)%(1<<31);return ctx.prng%args[0]
    raise ICLError('NAME','unknown builtin '+name)

def builtin(name,args,ctx):
    """Convert host primitive failures into bounded language diagnostics."""
    try:return _builtin(name,args,ctx)
    except (OverflowError,ZeroDivisionError):
        raise ICLError('NONFINITE','numeric primitive overflow or undefined finite result') from None
    except (TypeError,ValueError,KeyError,IndexError,AttributeError):
        raise ICLError('TYPE','malformed primitive input for '+str(name)) from None

BUILTINS={'len','abs','min','max','to_float','tensor','matmul','add','sub','mul','relu','tanh','normalize','softmax','reshape','sum','some','none_int','ok','err_int','unwrap','is_some','observer','context','provenance','represent','repr_value','repr_add','convert_frame','observe_mod','make_witness','recover','recover_without_witness','exact_value','approx','approx_value','request_effect','random_int'}
