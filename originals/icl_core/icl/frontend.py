"""ICL 0.1 hand-written lexer/parser. No host language parsing or evaluation."""
import bisect, json, re, unicodedata
from .runtime import ICLError

KEYWORDS={'module','import','fn','let','var','if','else','while','limit','return','true','false'}
class Parser:
    def __init__(self,source):
        if not isinstance(source,str) or len(source.encode())>1000000: raise ICLError('SOURCE_LIMIT','source must be UTF-8 text <= 1MB')
        for c in source:
            if unicodedata.category(c) in ('Cf','Cs') or (ord(c)<32 and c not in '\n\r\t'): raise ICLError('LEX','invisible/control character forbidden')
        self.source=source; self.tokens=[]; self.i=0; self.depth=0
        self.newlines=[-1]+[i for i,c in enumerate(source) if c=='\n']
        pattern=re.compile(r'(?P<space>\s+)|(?P<comment>//[^\n]*)|(?P<string>"(?:[^"\\\n]|\\["\\/bfnrt]|\\u[0-9a-fA-F]{4})*")|(?P<float>\d+\.\d+(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)|(?P<int>\d+)|(?P<id>[A-Za-z_][A-Za-z_0-9]*)|(?P<op>->|==|!=|<=|>=|&&|\|\||[{}()\[\],;:.+*/%<>=!\-])')
        p=0
        while p<len(source):
            m=pattern.match(source,p)
            if not m: raise ICLError('LEX',f'unexpected character {source[p]!r}',self.span(p))
            if m.lastgroup in ('int','float') and len(m.group())>128:
                raise ICLError('NUMBER_LIMIT','numeric token exceeds 128 characters',self.span(p))
            if m.lastgroup not in ('space','comment'): self.tokens.append((m.lastgroup,m.group(),self.span(p)))
            p=m.end()
        if len(self.tokens)>100000: raise ICLError('SOURCE_LIMIT','too many tokens')
        self.tokens.append(('eof','<eof>',self.span(len(source))))
    def span(self,p):
        line=bisect.bisect_left(self.newlines,p)
        return {'line':line,'column':p-self.newlines[line-1],'offset':p}
    def peek(self,v=None): return self.tokens[self.i][1] if v is None else self.tokens[self.i][1]==v
    def take(self,v=None):
        if self.i>=len(self.tokens) or self.tokens[self.i][0]=='eof':
            raise ICLError('PARSE','unexpected end of source',self.tokens[-1][2])
        t=self.tokens[self.i]
        if v is not None and t[1]!=v: raise ICLError('PARSE',f'expected {v}, got {t[1]}',t[2])
        self.i+=1; return t
    def ident(self):
        t=self.take()
        if t[0]!='id' or t[1] in KEYWORDS: raise ICLError('PARSE','identifier expected',t[2])
        return t[1]
    def typ(self):
        name=self.ident()
        if self.peek('['):
            self.take(); args=[]
            if not self.peek(']'):
                while True:
                    args.append(self.take()[1] if self.tokens[self.i][0]=='int' else self.typ())
                    if not self.peek(','): break
                    self.take(',')
            self.take(']'); name+='['+','.join(args)+']'
        return name
    def parse(self):
        self.take('module'); module=self.ident(); self.take(';'); imports=[]; funcs=[]
        while self.peek('import'):
            self.take(); imports.append(self.ident()); self.take(';')
        while not self.peek('<eof>'):
            sp=self.take('fn')[2]; name=self.ident(); self.take('('); params=[]
            if not self.peek(')'):
                while True:
                    nm=self.ident(); self.take(':'); params.append([nm,self.typ()])
                    if not self.peek(','): break
                    self.take(',')
            self.take(')'); self.take('->'); ret=self.typ(); funcs.append({'name':name,'params':params,'return_type':ret,'body':self.block(),'span':sp})
        if not funcs: raise ICLError('PARSE','module requires function')
        return {'module':module,'imports':imports,'functions':funcs}
    def block(self):
        self.take('{'); body=[]
        while not self.peek('}'):
            if self.peek('<eof>'): raise ICLError('PARSE','unterminated block')
            body.append(self.stmt())
        self.take('}'); return body
    def stmt(self):
        sp=self.tokens[self.i][2]; v=self.peek()
        if v in ('let','var'):
            self.take(); nm=self.ident(); tp=None
            if self.peek(':'): self.take();tp=self.typ()
            self.take('='); ex=self.expr();self.take(';');return {'kind':'let','name':nm,'type':tp,'mutable':v=='var','expr':ex,'span':sp}
        if v=='return':
            self.take();ex=self.expr();self.take(';');return {'kind':'return','expr':ex,'span':sp}
        if v=='if':
            self.take();co=self.expr();yes=self.block();no=[]
            if self.peek('else'):self.take();no=self.block()
            return {'kind':'if','cond':co,'then':yes,'else':no,'span':sp}
        if v=='while':
            self.take();co=self.expr();self.take('limit');t=self.take()
            if t[0]!='int' or not 0<=int(t[1])<=100000:raise ICLError('PARSE','loop limit must be literal 0..100000',t[2])
            return {'kind':'while','cond':co,'limit':int(t[1]),'body':self.block(),'span':sp}
        if self.tokens[self.i][0]=='id' and self.tokens[self.i+1][1]=='=':
            nm=self.ident();self.take('=');ex=self.expr();self.take(';');return {'kind':'assign','name':nm,'expr':ex,'span':sp}
        ex=self.expr();self.take(';');return {'kind':'expr','expr':ex,'span':sp}
    PREC={'||':1,'&&':2,'==':3,'!=':3,'<':4,'>':4,'<=':4,'>=':4,'+':5,'-':5,'*':6,'/':6,'%':6}
    def expr(self,p=0):
        self.depth+=1
        if self.depth>150:raise ICLError('PARSE_DEPTH','expression nesting exceeds 150')
        try:
            t=self.take();sp=t[2];v=t[1]
            if v=='-' and self.tokens[self.i][0]=='int' and self.tokens[self.i][1]==str(1<<63):
                self.take();left={'kind':'literal','value':-(1<<63),'span':sp}
            elif v in ('!','-'):left={'kind':'unary','op':v,'expr':self.expr(7),'span':sp}
            elif t[0] in ('int','float','string') or v in ('true','false'):
                val=json.loads(v) if t[0]=='string' else float(v) if t[0]=='float' else int(v) if t[0]=='int' else v=='true'
                if isinstance(val,str) and any(unicodedata.category(c)=='Cs' for c in val):raise ICLError('LEX','unpaired Unicode surrogate forbidden',sp)
                left={'kind':'literal','value':val,'span':sp}
            elif v=='(':
                left=self.expr()
                if self.peek(','):
                    items=[left]
                    while self.peek(','):self.take();items.append(self.expr())
                    left={'kind':'tuple','items':items,'span':sp}
                self.take(')')
            elif v=='[':
                items=[]
                if not self.peek(']'):
                    while True:
                        items.append(self.expr())
                        if not self.peek(','):break
                        self.take(',')
                self.take(']');left={'kind':'list','items':items,'span':sp}
            elif v=='{':
                fields={}
                if not self.peek('}'):
                    while True:
                        k=self.ident()
                        if k in fields:raise ICLError('PARSE','duplicate field')
                        self.take(':');fields[k]=self.expr()
                        if not self.peek(','):break
                        self.take(',')
                self.take('}');left={'kind':'record','fields':fields,'span':sp}
            elif t[0]=='id' and v not in KEYWORDS:left={'kind':'var','name':v,'span':sp}
            else:raise ICLError('PARSE','expression expected',sp)
            while True:
                if self.peek('('):
                    if left['kind'] not in ('var','field'):raise ICLError('PARSE','calls require named function',sp)
                    name=left['name'] if left['kind']=='var' else left['target']['name']+'.'+left['name'] if left['target']['kind']=='var' else None
                    if name is None:raise ICLError('PARSE','invalid call target',sp)
                    self.take();args=[]
                    if not self.peek(')'):
                        while True:
                            args.append(self.expr())
                            if not self.peek(','):break
                            self.take(',')
                    self.take(')');left={'kind':'call','name':name,'args':args,'span':sp};continue
                if self.peek('['):
                    self.take();ix=self.expr();self.take(']');left={'kind':'index','target':left,'index':ix,'span':sp};continue
                if self.peek('.'):
                    self.take();nm=self.ident();left={'kind':'field','target':left,'name':nm,'span':sp};continue
                op=self.peek();prec=self.PREC.get(op,-1)
                if prec<p:break
                self.take();right=self.expr(prec+1);left={'kind':'binary','op':op,'left':left,'right':right,'span':sp}
            return left
        finally:self.depth-=1

def parse(source):
    try:return Parser(source).parse()
    except RecursionError:raise ICLError('PARSE_DEPTH','parser recursion limit')
    except IndexError:raise ICLError('PARSE','unexpected end of source')
    except (ValueError,OverflowError):raise ICLError('LEX','invalid or oversized literal')

def canonical_ast(node):
    if isinstance(node,dict):return {k:canonical_ast(v) for k,v in sorted(node.items()) if k not in ('span','inferred_type','effects')}
    if isinstance(node,list):return [canonical_ast(v) for v in node]
    return node

def pretty(program):
    def e(x):
        k=x['kind']
        if k=='literal':return json.dumps(x['value'],ensure_ascii=False)
        if k=='var':return x['name']
        if k=='binary':return '('+e(x['left'])+' '+x['op']+' '+e(x['right'])+')'
        if k=='unary':return '('+x['op']+e(x['expr'])+')'
        if k=='call':return x['name']+'('+', '.join(e(a) for a in x['args'])+')'
        if k in ('list','tuple'):return ('[' if k=='list' else '(')+', '.join(e(a) for a in x['items'])+(']' if k=='list' else ')')
        if k=='record':return '{'+', '.join(n+': '+e(a) for n,a in x['fields'].items())+'}'
        if k=='index':return e(x['target'])+'['+e(x['index'])+']'
        if k=='field':return e(x['target'])+'.'+x['name']
        raise ICLError('UNSUPPORTED_OP',k)
    def b(ss):
        out=[]
        for s in ss:
            k=s['kind']
            if k=='let':out.append(('var ' if s['mutable'] else 'let ')+s['name']+(':'+s['type'] if s.get('type') else '')+' = '+e(s['expr'])+';')
            elif k=='assign':out.append(s['name']+' = '+e(s['expr'])+';')
            elif k=='return':out.append('return '+e(s['expr'])+';')
            elif k=='expr':out.append(e(s['expr'])+';')
            elif k=='if':out.append('if '+e(s['cond'])+' { '+b(s['then'])+' } else { '+b(s['else'])+' }')
            elif k=='while':out.append('while '+e(s['cond'])+' limit '+str(s['limit'])+' { '+b(s['body'])+' }')
        return ' '.join(out)
    return 'module '+program['module']+';\n'+''.join('import '+m+';\n' for m in program['imports'])+'\n'.join('fn '+f['name']+'('+', '.join(n+': '+t for n,t in f['params'])+') -> '+f['return_type']+' { '+b(f['body'])+' }' for f in program['functions'])+'\n'
