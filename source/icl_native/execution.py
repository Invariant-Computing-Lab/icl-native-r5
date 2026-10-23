"""Pure deterministic control/verification. No trained model or teaching oracle here.
These functions supply exact execution, not learned state prediction."""
from .common import ERRORS,validate_step
from .emitter import emit
from icl.runtime import checked_binary,checked_unary,ICLError
from icl.api import compile_source,run_ocir

def validate_plan(p):
    if type(p)!=dict or set(p)!={'initial','memory','steps'}:raise ValueError('PLAN_SCHEMA')
    if type(p['initial'])!=int or not -100000<=p['initial']<=100000:raise ValueError('INITIAL_RANGE')
    if p['memory'] is not None and (type(p['memory'])!=int or not -100000<=p['memory']<=100000):raise ValueError('MEMORY_RANGE')
    if type(p['steps'])!=list or not 1<=len(p['steps'])<=32:raise ValueError('STEP_LIMIT')
    for s in p['steps']:validate_step(s)

def protocol_guard(action,s,memory,journal_permission):
    """Trusted wrapper check; NEVER modifies a prediction or grants capability."""
    f=s['flags']
    if action=='TRANSLATE':
        for field,error in [('observer_match','OBSERVER_MISMATCH'),('frame_match','FRAME_MISMATCH'),('unit_match','UNIT_MISMATCH')]:
            if not f[field]:return error
    if action=='RESTORE':
        if not f['witness_present']:return 'NON_IDENTIFIABLE'
        if not f['witness_valid']:return 'WITNESS_CORRUPT'
    if action=='RECALL' and memory is None:return 'MEMORY_MISSING'
    if action=='JOURNAL' and (journal_permission is not True or f['journal_allowed'] is not True):return 'EFFECT_DENIED'
    return None

def advance_runtime(action,x,a,memory):
    """Normative runtime state transition using checked ICL primitives, not labels."""
    if action in ('ADD','TRANSLATE','RECORD_ADD','LIST_ADD'):x=checked_binary('+',x,a)
    elif action=='SUB':x=checked_binary('-',x,a)
    elif action=='MUL':x=checked_binary('*',x,a)
    elif action=='MAX':x=max(x,a)
    elif action=='MIN':x=min(x,a)
    elif action=='ABS':x=checked_unary('-',x) if x<0 else x
    elif action=='NEGATE':x=checked_unary('-',x)
    elif action=='REPEAT':
        for _ in range(3):x=checked_binary('+',x,a)
    elif action=='STORE':memory=x
    elif action=='RECALL':
        if memory is None:raise ValueError('MEMORY_MISSING')
        x=memory
    elif action not in ('RESTORE','JOURNAL'):raise ValueError('ACTION_UNKNOWN')
    return x,memory

def vm_verify(plan,pred,journal_permission=False,engine='vm'):
    if pred['guard_rejection'] is not None:return {'executed':False,'reason':'INDEPENDENT_GUARD_REJECTED','raw_prediction_preserved':True}
    actions=pred['actions']+[ERRORS[0]]*(len(plan['steps'])-len(pred['actions']))
    src=emit(plan,actions);ocir=compile_source(src)
    out=run_ocir(ocir,args=[plan['initial'],plan['memory'] or 0],engine=engine,policy={'journal':{'allow':journal_permission is True}})
    return {'executed':True,'source_program':src,'ocir':ocir,'result':out,'runtime_consistency':out['value']==pred['composed_result']}

