from pathlib import Path
import json,hashlib
p=Path(__file__).parent/'source'/'icl_core'
f=p/'icl/frontend.py';s=f.read_text();s=s.replace("'true','false'}","'true','false','type'}")
s=s.replace('self.source=source; self.tokens=[]; self.i=0; self.depth=0','self.source=source; self.tokens=[]; self.i=0; self.depth=0; self.aliases={}')
s=s.replace("        name=self.ident()\n        if self.peek('['):", """        name=self.ident()
        if name in self.aliases:
            if self.peek('[') or self.peek('{'):
                raise ICLError('TYPE','type alias cannot take arguments')
            return self.aliases[name]
        if name=='Record' and self.peek('{'):
            self.take('{'); fields={}
            if self.peek('}'):raise ICLError('TYPE','empty record annotation is unsupported')
            while True:
                field=self.ident()
                if field in fields:raise ICLError('TYPE','duplicate record type field')
                self.take(':'); fields[field]=self.typ()
                if not self.peek(','):break
                self.take(',')
            self.take('}')
            return 'Record{'+','.join(k+':'+v for k,v in sorted(fields.items()))+'}'
        if self.peek('['):""")
s=s.replace("        while not self.peek('<eof>'):\n            sp=self.take('fn')", """        while self.peek('type'):
            self.take('type'); alias=self.ident()
            if alias in self.aliases or alias in {'Int64','Float64','Bool','String','Record','Tensor','List','Result','Option','Observer','Context','ProvenanceRef','RecoveryWitness','Capability','Tuple','Exact','Approx','Representation'}:
                raise ICLError('TYPE','duplicate or reserved type alias')
            self.take('='); target=self.typ(); self.take(';')
            from .checker import valid_type
            if not valid_type(target):raise ICLError('TYPE','alias must resolve to an already defined type')
            self.aliases[alias]=target
        while not self.peek('<eof>'):
            sp=self.take('fn')""")
f.write_text(s)
f=p/'icl/checker.py';s=f.read_text();s=s.replace("    if t in BASIC:return True", """    if not isinstance(t,str) or len(t)>8192:return False
    if t in BASIC:return True
    if t.startswith('Record{') and t.endswith('}'):
        try:
            pairs=[x.split(':',1) for x in split_types(t[7:-1])]
            if not pairs or any(len(x)!=2 for x in pairs):return False
            names=[x[0] for x in pairs]
            return len(set(names))==len(names) and names==sorted(names) and all(re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',k) and valid_type(v) for k,v in pairs)
        except (ValueError,RecursionError):return False""")
s=s.replace('    def ex(x,env):','    def ex(x,env,expected=None):')
s=s.replace("            ts=[ex(y,env) for y in x['items']]\n            if not ts:raise ICLError('TYPE','empty literal needs unsupported explicit type; use nonempty literals',sp)","""            inner=expected[5:-1] if k=='list' and isinstance(expected,str) and expected.startswith('List[') and valid_type(expected) else None
            ts=[ex(y,env,inner) for y in x['items']]
            if not ts:
                if k=='list' and inner is not None:
                    x['inferred_type']=expected
                    return expected
                raise ICLError('TYPE','empty list requires a contextual List type',sp)""")
s=s.replace("            nm=x['name'];args=x['args'];ts=[ex(y,env) for y in args]", """            nm=x['name'];args=x['args']
            expected_args=[t for _,t in fs[nm]['params']] if nm in fs else []
            ts=[ex(y,env,expected_args[i] if i<len(expected_args) else None) for i,y in enumerate(args)]""")
s=s.replace("                t=ex(s['expr'],env)","                t=ex(s['expr'],env,s.get('type'))")
s=s.replace("                same(ex(s['expr'],env),t,sp)","                same(ex(s['expr'],env,t),t,sp)")
s=s.replace("elif k=='return':same(ex(s['expr'],env),ret,sp)","elif k=='return':same(ex(s['expr'],env,ret),ret,sp)")
f.write_text(s)
f=p/'icl/api.py';s=f.read_text().replace("SCHEMA_VERSION='0.1.0'","SCHEMA_VERSION='0.2.1'")
s=s.replace("'policy_effect','checkpoint']","'policy_effect','checkpoint','record_annotations','type_aliases','contextual_empty_lists']")
f.write_text(s)
for n in ('OCIR_SCHEMA.json','icl/OCIR_SCHEMA.json'):
 f=p/n;o=json.loads(f.read_text());o['schema_version']='0.2.1';o['properties']['schema_version']['const']='0.2.1';f.write_text(json.dumps(o,separators=(',',':'))+'\n')
f=p/'icl/__init__.py';s=f.read_text().replace('0.1.0','0.2.1');f.write_text(s)
# Package metadata must identify the new source version, not the frozen wheel.
for n in ('pyproject.toml','setup.py','setup.cfg'):
 f=p/n
 if f.exists():f.write_text(f.read_text().replace('0.1.0','0.2.1'))
print('Patched source copy to 0.2.1; originals untouched')
