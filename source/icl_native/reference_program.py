"""Generic input-task reference: context remains runtime data, not pre-folded labels.
Independent from the neural ACTIONS table and deterministic candidate emitter.
The full plan has meaningful alternate-context branches; no uniqueness padding.
"""
from .common import FLAGS

def reference_source(plan):
 head='''module reference_task;
type ContextFlags = Record{'''+','.join(k+':Bool' for k in sorted(FLAGS))+'''};
type Pair = Record{delta:Int64,value:Int64};
fn record_sum(p:Pair)->Int64 {return p.value+p.delta;}
fn main(initial:Int64,initial_memory:Int64,initial_has_memory:Bool,ctx:List[ContextFlags])->Result[Int64] {
 var x=initial;var memo=initial_memory;var has_memory=initial_has_memory;
'''
 code=[head]
 for j,s in enumerate(plan['steps']):
  name=s['intent'];a='('+str(s['arg'])+')';c=f'ctx[{j}]'
  if name=='increase':v=f'x=x+{a};'
  elif name=='decrease':v=f'x=x-{a};'
  elif name=='scale':v=f'x=x*{a};'
  elif name=='floor':v=f'x=max(x,{a});'
  elif name=='ceiling':v=f'x=min(x,{a});'
  elif name=='magnitude':v='x=abs(x);'
  elif name=='repeat':v=f'var k{j}=0;while k{j}<3 limit 3 {{x=x+{a};k{j}=k{j}+1;}}'
  elif name=='translate':v=f'''if !{c}.observer_match {{return err_int("OBSERVER_MISMATCH");}}
if !{c}.frame_match {{return err_int("FRAME_MISMATCH");}}
if !{c}.unit_match {{return err_int("UNIT_MISMATCH");}}
let l{j}=represent(x,"main","scalar","unit");let r{j}=represent({a},"main","scalar","unit");x=repr_value(repr_add(l{j},r{j}));'''
  elif name=='restore':v=f'''if !{c}.witness_present {{return err_int("NON_IDENTIFIABLE");}}
if !{c}.witness_valid {{return err_int("WITNESS_CORRUPT");}}
let obs{j}=observe_mod(x,{s['modulus']},"main");let wit{j}=make_witness(x,{s['modulus']});x=exact_value(recover(obs{j},wit{j}));'''
  elif name=='remember':v='memo=x;has_memory=true;'
  elif name=='recall':v='if !has_memory {return err_int("MEMORY_MISSING");} x=memo;'
  elif name=='journal':v=f'if !{c}.journal_allowed {{return err_int("EFFECT_DENIED");}} let e{j}=request_effect("journal","step_{j}");'
  elif name=='conditional':v=f'if {c}.condition {{x=x+{a};}} else {{x=x-{a};}}'
  elif name=='record_add':v=f'x=record_sum({{delta:{a},value:x}});'
  elif name=='list_add':v=f'let items{j}=[x,{a}];x=items{j}[0]+items{j}[1];'
  elif name=='axis_reverse':v='x=-x;'
  else:raise ValueError('UNSUPPORTED_REFERENCE_INTENT')
  code.append(v)
 return '\n'.join(code)+'\nreturn ok(x);}\n'

def reference_arguments(p):
 return [p['initial'],p['memory'] or 0,p['memory'] is not None,[s['flags'] for s in p['steps']]]
