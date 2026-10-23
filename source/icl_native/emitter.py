"""Deterministic, audited ICL code emitter. Syntax is supplied here, not learned.
No oracle/ground-truth label is imported. Model actions alone select operations.
"""
from __future__ import annotations
import json
from .common import ACTIONS,ERRORS,validate_step
HEADER='''module native_plan;
type Pair = Record{delta:Int64,value:Int64};
fn record_sum(p:Pair)->Int64 {return p.value+p.delta;}
fn main(initial:Int64, initial_memory:Int64)->Result[Int64] {
var x = initial; var memo = initial_memory;
'''

def emit(plan:dict,actions:list[str])->str:
    if len(actions)!=len(plan['steps']) or not 1<=len(actions)<=32:raise ValueError('ACTION_LENGTH')
    parts=[HEADER]
    for j,(s,action) in enumerate(zip(plan['steps'],actions)):
        validate_step(s)
        if action not in ACTIONS:raise ValueError('ACTION_UNKNOWN')
        a=s['arg'];lit=str(a);f=s['flags']
        if action in ERRORS:
            parts.append('return err_int('+json.dumps(action)+');');break
        if action=='ADD':code=f'x=x+({lit});'
        elif action=='SUB':code=f'x=x-({lit});'
        elif action=='MUL':code=f'x=x*({lit});'
        elif action=='MAX':code=f'x=max(x,({lit}));'
        elif action=='MIN':code=f'x=min(x,({lit}));'
        elif action=='ABS':code='x=abs(x);'
        elif action=='NEGATE':code='x=-x;'
        elif action=='REPEAT':code=f'var k{j}=0; while k{j}<3 limit 3 {{x=x+({lit}); k{j}=k{j}+1;}}'
        elif action=='STORE':code='memo=x;'
        elif action=='RECALL':code='x=memo;'
        elif action=='JOURNAL':code=f'let permitted{j}=request_effect("journal","step_{j}");'
        elif action=='RECORD_ADD':code=f'x=record_sum({{delta:({lit}),value:x}});'
        elif action=='LIST_ADD':code=f'let items{j}=[x,({lit})]; x=items{j}[0]+items{j}[1];'
        elif action=='TRANSLATE':
            ob='main' if f['observer_match'] else 'other';fr='scalar' if f['frame_match'] else 'other';un='unit' if f['unit_match'] else 'other'
            code=f'let left{j}=represent(x,"main","scalar","unit"); let right{j}=represent(({lit}),"{ob}","{fr}","{un}"); x=repr_value(repr_add(left{j},right{j}));'
        elif action=='RESTORE':
            # Synthetic known-state roundtrip: witness is made from x, not recovered from unknown data.
            # The wrapper checks supplied boolean scenario conditions, NOT an external witness signature.
            code=f'let r{j}=observe_mod(x,{s["modulus"]},"main"); let w{j}=make_witness(x,{s["modulus"]}); x=exact_value(recover(r{j},w{j}));'
        else:raise ValueError('UNSUPPORTED_ACTION')
        parts.append(code)
    parts.append('return ok(x); }')
    return '\n'.join(parts)+'\n'
