"""Post-training robustness audit. All Boolean contexts, sampled numeric boundaries.
This is not a proof over all numeric inputs and is not used to tune the models.
"""
from pathlib import Path
import sys,itertools,time
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'source'),str(R/'source/icl_core')]
import numpy as np,torch
from icl_native.common import *
from icl_native.checkpoint import load_checkpoint
base=[];labels=[];keys=[]
for intent in INTENTS:
 for bits in itertools.product([False,True],repeat=8):
  s={'intent':intent,'arg':0,'modulus':2,'flags':dict(zip(FLAGS,bits))}
  base.append(features(s,0,bits[5])[:24]);labels.append(ACTIONS.index(oracle_action(s,bits[5])));keys.append((intent,bits))
base=np.asarray(base,dtype=np.float32);labels=np.asarray(labels);torch.set_num_threads(1)
grid=list(itertools.product([-100000,-999,-1,0,1,999,100000],range(-3,4),[2,7,11]));start=time.time();results={}
for seed in (17,29,43):
 m,meta=load_checkpoint(R/'models'/f'native_{seed}'/'best');total=bad=0;errors=[];confusion=np.zeros((len(ACTIONS),len(ACTIONS)),dtype=np.int64)
 with torch.no_grad():
  for x,a,mod in grid:
   n=np.asarray(features({'intent':INTENTS[0],'arg':a,'modulus':mod,'flags':{k:False for k in FLAGS}},x,False)[24:],dtype=np.float32)
   X=np.concatenate([base,np.broadcast_to(n,(len(base),6))],axis=1);pred=m(torch.from_numpy(X)).argmax(-1).numpy();ix=np.where(pred!=labels)[0];total+=len(labels);bad+=len(ix);np.add.at(confusion,(labels,pred),1)
   for i in ix[:max(0,30-len(errors))]:errors.append({'intent':keys[i][0],'effective_flags':dict(zip(FLAGS,keys[i][1])),'value':x,'arg':a,'modulus':mod,'expected':ACTIONS[labels[i]],'predicted':ACTIONS[pred[i]]})
 results[str(seed)]={'total_cases':total,'incorrect':bad,'accuracy':1-bad/total,'first_mismatches':errors,'confusion':confusion.tolist()}
 print(seed,total,bad,flush=True)
dump(R/'reports/BOOLEAN_CONTEXT_GRID.json',{'audit':'all 16 intents x 256 effective Boolean contexts x 147 sampled numeric combinations','models_unchanged':True,'training_not_repeated':'post-training robustness only','numeric_grid':{'initial':[-100000,-999,-1,0,1,999,100000],'arg':list(range(-3,4)),'modulus':[2,7,11]},'all_contexts_but_not_all_numeric_values':True,'results':results,'elapsed_seconds':time.time()-start})
