import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from icl.api import run_source,compile_source,run_ocir,loads_ocir,dumps_ocir
from icl.runtime import ICLError,digest
records=[]
for p in sorted((ROOT/'examples').glob('*.icl')):
    source=p.read_text();mods=json.loads((ROOT/'examples/module_map.json').read_text()) if 'module_main' in p.name else None
    rec={'name':p.name,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'runs':{}}
    for engine in ('tree','vm'):
        try:
            out=run_source(source,engine=engine,module_map=mods);rec['runs'][engine]={'value':out['value'],'effects':out['effects'],'steps':out['steps'],'trace_sha256':digest(out['trace'])}
        except ICLError as e:rec['runs'][engine]={'expected_error':e.code}
    rec['parity']=rec['runs']['tree'].get('value')==rec['runs']['vm'].get('value') and rec['runs']['tree'].get('expected_error')==rec['runs']['vm'].get('expected_error')
    if 'checkpoint' in p.name:
        o=compile_source(source);paused=run_ocir(o,stop_after=20);resumed=run_ocir(loads_ocir(dumps_ocir(o)),checkpoint=json.loads(json.dumps(paused['checkpoint'])));full=run_ocir(o)
        rec['checkpoint_replay_full_parity']=resumed==full
    records.append(rec)
(ROOT/'evidence/DEMO_RESULTS.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps({'demos':len(records),'parity':all(r['parity'] for r in records),'checkpoint_replay':all(r.get('checkpoint_replay_full_parity',True) for r in records)}))
