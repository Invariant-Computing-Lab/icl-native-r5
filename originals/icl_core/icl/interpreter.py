"""Independent recursive tree evaluator: no bytecode compiler or VM calls."""
from .runtime import ICLError,RuntimeContext,checked_binary,checked_unary,builtin,BUILTINS,digest
from .checker import validate_value
class Returned(Exception):
    def __init__(self,value):self.value=value
class Scope:
    def __init__(self,parent=None):self.parent=parent;self.values={}
    def get(self,name):
        if name in self.values:return self.values[name]
        if self.parent is not None:return self.parent.get(name)
        raise ICLError('NAME','undefined '+name)
    def set(self,name,val):
        if name in self.values:self.values[name]=val
        elif self.parent is not None:self.parent.set(name,val)
        else:raise ICLError('NAME','undefined assignment '+name)

def execute_tree(program,entry='main',args=None,limits=None,policy=None):
    ctx=RuntimeContext(limits,policy);fs={f['name']:f for f in program['functions']};depth=0
    def ex(x,scope):
        chain=[];cur=scope
        while cur is not None:chain.append(cur.values);cur=cur.parent
        ctx.step('tree.'+x['kind'],inputs={'scope':chain,'prng':ctx.prng})
        event=ctx.trace[-1]
        try:
            value=_ex(x,scope);event['output_hash']=digest(value);event['state_ref']=event['output_hash'];return value
        except ICLError as error:event['error_code']=error.code;raise
    def _ex(x,scope):
        k=x['kind']
        if k=='literal':return x['value']
        if k=='var':return scope.get(x['name'])
        if k=='unary':return checked_unary(x['op'],ex(x['expr'],scope))
        if k=='binary':
            a=ex(x['left'],scope)
            if x['op']=='&&' and a is False:return False
            if x['op']=='||' and a is True:return True
            return ctx.check_value(checked_binary(x['op'],a,ex(x['right'],scope)))
        if k=='call':
            aa=[ex(v,scope) for v in x['args']]
            return ctx.check_value(builtin(x['name'],aa,ctx) if x['name'] in BUILTINS else call(x['name'],aa))
        if k in ('list','tuple'):return ctx.check_value([ex(v,scope) for v in x['items']])
        if k=='record':return ctx.check_value({n:ex(x['fields'][n],scope) for n in sorted(x['fields'])})
        if k=='index':
            a=ex(x['target'],scope);i=ex(x['index'],scope)
            if i<0 or i>=len(a):raise ICLError('BOUNDS','index out of bounds')
            return a[i]
        if k=='field':return ex(x['target'],scope)[x['name']]
        raise ICLError('UNSUPPORTED_OP',k)
    def block(ss,parent):
        scope=Scope(parent)
        for s in ss:
            k=s['kind'];ctx.step('tree.'+k)
            if k=='let':scope.values[s['name']]=ex(s['expr'],scope)
            elif k=='assign':scope.set(s['name'],ex(s['expr'],scope))
            elif k=='return':raise Returned(ex(s['expr'],scope))
            elif k=='expr':ex(s['expr'],scope)
            elif k=='if':block(s['then'] if ex(s['cond'],scope) else s['else'],scope)
            elif k=='while':
                count=0
                while ex(s['cond'],scope):
                    if count>=s['limit']:raise ICLError('LOOP_LIMIT','declared iteration bound exceeded')
                    count+=1;block(s['body'],scope)
            else:raise ICLError('UNSUPPORTED_OP',k)
    def call(name,aa):
        nonlocal depth
        if name not in fs:raise ICLError('NAME','entry/function missing '+name)
        f=fs[name]
        if len(aa)!=len(f['params']):raise ICLError('TYPE','function argument count')
        depth+=1
        if depth>ctx.limits['max_stack']:raise ICLError('STACK_LIMIT','call stack budget')
        env=Scope()
        for (n,t),v in zip(f['params'],aa):validate_value(v,t,ctx);env.values[n]=v
        try:block(f['body'],env)
        except Returned as r:validate_value(r.value,f['return_type'],ctx);return r.value
        finally:depth-=1
        raise ICLError('RETURN','function reached end')
    try:value=call(entry,args or [])
    except RecursionError:raise ICLError('STACK_LIMIT','host recursion boundary reached')
    ctx.check_value(value)
    return {'value':value,'trace':ctx.trace,'effects':ctx.effects,'steps':ctx.steps}
