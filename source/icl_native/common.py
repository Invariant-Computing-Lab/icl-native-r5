from __future__ import annotations
import hashlib,json,math,os
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
INTENTS=['increase','decrease','scale','floor','ceiling','magnitude','repeat','translate','restore','remember','recall','journal','conditional','record_add','list_add','axis_reverse']
FLAGS=['observer_match','frame_match','unit_match','witness_present','witness_valid','memory_present','journal_allowed','condition']
ERRORS=['OBSERVER_MISMATCH','FRAME_MISMATCH','UNIT_MISMATCH','NON_IDENTIFIABLE','WITNESS_CORRUPT','MEMORY_MISSING','EFFECT_DENIED']
ACTIONS=['ADD','SUB','MUL','MAX','MIN','ABS','REPEAT','TRANSLATE','RESTORE','STORE','RECALL','JOURNAL','RECORD_ADD','LIST_ADD','NEGATE']+ERRORS
FEATURE_NAMES=['intent:'+s for s in INTENTS]+['flag:'+s for s in FLAGS]+['nuisance:'+s for s in ['value','arg','modulus','parity','residue3','residue5']]
D=len(FEATURE_NAMES);K=len(ACTIONS);H=32

def canonical(x:Any)->str:return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x:Any)->str:return hashlib.sha256(canonical(x).encode()).hexdigest()
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p:Path,x:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def strict_load(p:Path,max_bytes:int=8_000_000)->Any:
    if p.stat().st_size>max_bytes:raise ValueError('INPUT_SIZE_LIMIT')
    def pairs(xs):
        d={}
        for k,v in xs:
            if k in d:raise ValueError('DUPLICATE_JSON_KEY')
            d[k]=v
        return d
    def finite_float(s):
        x=float(s)
        if not math.isfinite(x):raise ValueError('NONFINITE')
        return x
    return json.loads(p.read_text(),object_pairs_hook=pairs,parse_float=finite_float,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE')))

def validate_step(s:dict)->None:
    if type(s)!=dict or set(s)!={'intent','arg','modulus','flags'}:raise ValueError('STEP_SCHEMA')
    if s['intent'] not in INTENTS:raise ValueError('UNSUPPORTED_INTENT')
    if type(s['arg'])!=int or not -3<=s['arg']<=3:raise ValueError('ARG_RANGE')
    if type(s['modulus'])!=int or not 2<=s['modulus']<=11:raise ValueError('MODULUS_RANGE')
    if type(s['flags'])!=dict or set(s['flags'])!=set(FLAGS) or any(type(v)!=bool for v in s['flags'].values()):raise ValueError('FLAGS_SCHEMA')

def features(s:dict,x:int,memory_present:bool)->list[float]:
    f=dict(s['flags']);f['memory_present']=memory_present
    return [float(s['intent']==i) for i in INTENTS]+[float(f[k]) for k in FLAGS]+[math.tanh(x/50),s['arg']/3,s['modulus']/11,float(x%2),x%3/2,x%5/4]

def oracle_action(s:dict,memory_present:bool)->str:
    """Supervision ONLY. Never called by production prediction or its encoder."""
    i=s['intent'];f=s['flags']
    if i=='translate':
        for flag,err in [('observer_match','OBSERVER_MISMATCH'),('frame_match','FRAME_MISMATCH'),('unit_match','UNIT_MISMATCH')]:
            if not f[flag]:return err
    if i=='restore':
        if not f['witness_present']:return 'NON_IDENTIFIABLE'
        if not f['witness_valid']:return 'WITNESS_CORRUPT'
    if i=='recall' and not memory_present:return 'MEMORY_MISSING'
    if i=='journal' and not f['journal_allowed']:return 'EFFECT_DENIED'
    if i=='conditional':return 'ADD' if f['condition'] else 'SUB'
    return {'increase':'ADD','decrease':'SUB','scale':'MUL','floor':'MAX','ceiling':'MIN','magnitude':'ABS','repeat':'REPEAT','translate':'TRANSLATE','restore':'RESTORE','remember':'STORE','recall':'RECALL','journal':'JOURNAL','record_add':'RECORD_ADD','list_add':'LIST_ADD','axis_reverse':'NEGATE'}[i]

def scalar_reference(action:str,x:int,a:int,memory:int|None)->tuple[int,int|None]:
    """Independent finite arithmetic oracle, used only by datasets/evaluation."""
    if action in ERRORS:return x,memory
    if action in ('ADD','TRANSLATE','RECORD_ADD','LIST_ADD'):x+=a
    elif action=='SUB':x-=a
    elif action=='MUL':x*=a
    elif action=='MAX':x=max(x,a)
    elif action=='MIN':x=min(x,a)
    elif action=='ABS':x=abs(x)
    elif action=='REPEAT':x+=3*a
    elif action=='NEGATE':x=-x
    elif action=='STORE':memory=x
    elif action=='RECALL':
        if memory is None:raise ValueError('MEMORY_MISSING')
        x=memory
    elif action not in ('RESTORE','JOURNAL'):raise ValueError('UNSUPPORTED_ACTION')
    if not -(1<<63)<=x<(1<<63):raise OverflowError('INT64')
    return x,memory

def target_steps(plan:dict):
    x=plan['initial'];mem=plan['memory'];allfeat=[];labels=[];states=[];first_error=None;prefix=True
    for i,s in enumerate(plan['steps']):
        a=oracle_action(s,mem is not None);allfeat.append(features(s,x,mem is not None));labels.append(ACTIONS.index(a));states.append(x)
        if a in ERRORS:
            if first_error is None:first_error=(i,a)
        else:x,mem=scalar_reference(a,x,s['arg'],mem)
    # Actual program stops at its first error. Labels after it are auxiliary independent local supervision only.
    if first_error:return allfeat,labels,{'tag':'Err','error':first_error[1]},first_error[0]+1,states
    return allfeat,labels,{'tag':'Ok','value':x},len(labels),states
