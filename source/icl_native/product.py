"""Local bounded product: learned proposals -> independent guards -> ICL VM.
Structured-plan input, not free-form language. Exact state is executor state;
this module makes no claim that numerical arithmetic is a learned prediction.
"""
from __future__ import annotations
import argparse,copy,json,sys
from pathlib import Path
import torch
from .common import ROOT,ACTIONS,ERRORS,FEATURE_NAMES,features,validate_step,strict_load,canonical,dump
from .checkpoint import load_checkpoint
from .train import mask_input
from .emitter import emit
from icl.runtime import checked_binary,checked_unary,ICLError
from icl.api import compile_source,run_ocir,dumps_ocir,loads_ocir

from .execution import validate_plan,protocol_guard,advance_runtime,vm_verify

@torch.no_grad()
def predict_many(model,plans,kind='native',journal_permission=False):
    """Batched online decisions; later states follow PREDICTED actions, not oracle states."""
    model.eval();n=len(plans);xs=[p['initial'] for p in plans];mem=[p['memory'] for p in plans]
    preds=[[] for _ in plans];confs=[[] for _ in plans];results=[None]*n;guards=[None]*n;journal_attempt=[0]*n;journal_allowed=[0]*n
    for j in range(max(len(p['steps']) for p in plans)):
        ids=[i for i,p in enumerate(plans) if j<len(p['steps']) and results[i] is None]
        if not ids:break
        rows=[]
        for i in ids:
            step=copy.deepcopy(plans[i]['steps'][j]);step['flags']['journal_allowed']=journal_permission is True and step['flags']['journal_allowed'] is True
            rows.append(features(step,xs[i],mem[i] is not None))
        logits=model(mask_input(torch.tensor(rows,dtype=torch.float32),kind));pr=logits.softmax(-1);act=pr.argmax(-1).tolist();prob=pr.max(-1).values.tolist()
        for i,a,c in zip(ids,act,prob):
            action=ACTIONS[a];s=plans[i]['steps'][j];preds[i].append(action);confs[i].append(c)
            if action in ERRORS:results[i]={'tag':'Err','error':action};continue
            if action=='JOURNAL':journal_attempt[i]+=1
            err=protocol_guard(action,s,mem[i],journal_permission)
            if err:guards[i]={'step':j,'reason':err};results[i]={'tag':'Err','error':err};continue
            try:xs[i],mem[i]=advance_runtime(action,xs[i],s['arg'],mem[i])
            except (ICLError,OverflowError,ValueError) as e:results[i]={'tag':'Err','error':getattr(e,'code',str(e))};guards[i]={'step':j,'reason':results[i]['error']};continue
            if action=='JOURNAL':journal_allowed[i]+=1
    for i in range(n):
        if results[i] is None:results[i]={'tag':'Ok','value':xs[i]}
    return [{'actions':a,'confidence':min(c) if c else 0.0,'composed_result':v,'guard_rejection':g,'journal_attempts':att,'journal_allow_decisions':ok,'execution_scope':'host state simulation; actual ICL effects are in verification.result.effects'} for a,c,v,g,att,ok in zip(preds,confs,results,guards,journal_attempt,journal_allowed)]

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--permit-local-journal',action='store_true')
    a=p.parse_args()
    try:
        req=strict_load(a.request,100000);validate_plan(req);torch.set_num_threads(1);model,meta=load_checkpoint(a.model)
        pred=predict_many(model,[req],meta['kind'],a.permit_local_journal)[0];checked=vm_verify(req,pred,a.permit_local_journal)
        answer={'model_kind':meta['kind'],'model_seed':meta['seed'],'scope':'bounded structured-plan learned opcode compiler','proposal':pred,'verification':checked,'neural_contribution':'opcode/guard selection','deterministic_contribution':'input encoding, composition control, source syntax, guards, exact execution','confidence_is_uncalibrated':True}
        if a.output:dump(a.output,answer)
        print(canonical(answer));return 0
    except (ValueError,OSError,KeyError,ICLError) as e:
        print(canonical({'status':'ERROR','reason':str(e)}),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
