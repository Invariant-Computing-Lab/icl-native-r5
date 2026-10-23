import sys,json
from pathlib import Path
from icl.api import compile_source,run_ocir,dumps_ocir,loads_ocir
p=Path(sys.argv[2]);mode=sys.argv[1]
if mode=='save':
 s='module test; fn main()->Int64 {var x=0; while x<4 limit 4 {x=x+1;} return x;}'
 o=compile_source(s);p.with_suffix('.ocir').write_text(dumps_ocir(o));a=run_ocir(o,stop_after=6);p.write_text(json.dumps(a['checkpoint']));p.with_suffix('.full').write_text(json.dumps(run_ocir(o)))
else:
 o=loads_ocir(p.with_suffix('.ocir').read_text());a=run_ocir(o,checkpoint=json.loads(p.read_text()));b=json.loads(p.with_suffix('.full').read_text());assert a['value']==b['value'] and a['trace']==b['trace'];print('SEPARATE_PROCESS_REPLAY_PASS')
