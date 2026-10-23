"""Training reads only train and validation. Test access is in a separate module."""
from __future__ import annotations
import os,time,sys,json,copy,resource
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from .common import *
from .graph import *
from .checkpoint import save_checkpoint,load_checkpoint

def mask_input(x,kind):
    if kind not in ('no_context','no_witness','no_memory'):return x
    x=x.clone()
    columns={'no_context':[16,17,18,22,23],'no_witness':[19,20],'no_memory':[21]}[kind]
    x[:,columns]=0
    return x

def step_once(model,opt,x,y,kind,gen,batch=2048):
    idx=torch.randint(len(x),(min(batch,len(x)),),generator=gen);a=mask_input(x[idx],kind);b=a.clone()
    b[:,24:]=torch.rand(b.shape[0],6,generator=gen)*2-1
    model.train();opt.zero_grad(set_to_none=True);la=model(a);lb=model(b)
    loss=F.cross_entropy(la,y[idx])+F.cross_entropy(lb,y[idx])
    if kind not in ('flat','no_invariance'):loss=loss+.15*(la.softmax(-1)-lb.softmax(-1)).square().mean()
    if not torch.isfinite(loss):raise FloatingPointError('NONFINITE_LOSS')
    loss.backward()
    grads=[p.grad for p in model.parameters() if p.grad is not None]
    if not grads or any(not torch.isfinite(g).all() for g in grads):raise FloatingPointError('NONFINITE_GRADIENT')
    opt.step();return float(loss.detach())

def evaluate_val(model,x,y,kind):
    model.eval();total=correct=0;loss=0.
    with torch.no_grad():
        for a,b in zip(x.split(4096),y.split(4096)):
            logits=model(mask_input(a,kind));loss+=float(F.cross_entropy(logits,b,reduction='sum'));correct+=int((logits.argmax(-1)==b).sum());total+=len(b)
    return {'loss':loss/total,'accuracy':correct/total,'n_nodes':total}

def train_one(kind,seed,epochs=20):
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True);torch.manual_seed(seed)
    root=ROOT/'models'/f'{kind}_{seed}'
    if (root/'TRAINING_REPORT.json').exists():return strict_load(root/'TRAINING_REPORT.json')
    root.mkdir(parents=True,exist_ok=True)
    with np.load(ROOT/'data/train.npz',allow_pickle=False) as z:x=torch.from_numpy(z['X']);y=torch.from_numpy(z['y'])
    with np.load(ROOT/'data/validation.npz',allow_pickle=False) as z:vx=torch.from_numpy(z['X']);vy=torch.from_numpy(z['y'])
    model=model_for(kind);opt=torch.optim.Adam(model.parameters(),lr=.003);gen=torch.Generator().manual_seed(seed+1000)
    initial={k:v.detach().clone() for k,v in model.state_dict().items()};save_checkpoint(root/'initial',model,opt,kind,seed,0,0,gen)
    batches=(len(x)+2047)//2048;best=float('inf');best_epoch=0;step=0;start=time.time();all_logs=[]
    for epoch in range(1,epochs+1):
        losses=[]
        for _ in range(batches):losses.append(step_once(model,opt,x,y,kind,gen));step+=1
        val=evaluate_val(model,vx,vy,kind);rec={'epoch':epoch,'step':step,'train_loss':sum(losses)/len(losses),'validation':val,'elapsed_seconds':time.time()-start};all_logs.append(rec)
        with (root/'training_log.jsonl').open('a') as f:f.write(canonical(rec)+'\n')
        if val['loss']<best:best=val['loss'];best_epoch=epoch;save_checkpoint(root/'best',model,opt,kind,seed,epoch,step,gen)
        if epoch%5==0:save_checkpoint(root/f'epoch_{epoch:02d}',model,opt,kind,seed,epoch,step,gen)
    # Verify full optimizer+RNG continuation by repeating the same next stochastic update.
    save_checkpoint(root/'final',model,opt,kind,seed,epochs,step,gen)
    model1,meta1,opt1,g1=load_checkpoint(root/'final',True);l1=step_once(model1,opt1,x,y,kind,g1)
    model2,meta2,opt2,g2=load_checkpoint(root/'final',True);l2=step_once(model2,opt2,x,y,kind,g2)
    resume_diff=max(float((model1.state_dict()[k]-model2.state_dict()[k]).abs().max()) for k in model1.state_dict())
    if resume_diff!=0 or l1!=l2:raise AssertionError('RESUME_PARITY')
    changed=any(not torch.equal(v,initial[k]) for k,v in model.state_dict().items())
    report={'run_id':f'R5_{kind}_{seed}','kind':kind,'seed':seed,'epochs':epochs,'optimizer_steps':step,'parameter_count':sum(p.numel() for p in model.parameters()),'training_nodes':len(x),'validation_nodes':len(vx),'best_validation_epoch':best_epoch,'best_validation_ce':best,'weights_changed':changed,'initial_weights_sha256':sha(root/'initial/weights.safetensors'),'final_weights_sha256':sha(root/'final/weights.safetensors'),'selected_weights_sha256':sha(root/'best/weights.safetensors'),'all_losses_gradients_finite':True,'optimizer_rng_resume_max_abs':resume_diff,'optimizer_rng_resume_loss_equal':l1==l2,'elapsed_seconds':time.time()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'test_read':False,'training_code_sha256':sha(Path(__file__)),'dataset_manifest_sha256':sha(ROOT/'data/DATA_MANIFEST.json'),'protocol_sha256':sha(ROOT/'reports/PRECOMMITTED_PROTOCOL.json'),'torch_version':torch.__version__}
    dump(root/'TRAINING_REPORT.json',report);print(canonical(report),flush=True);return report

def main():
    (ROOT/'source/model.icl').write_text(model_source());dump(ROOT/'source/compiled_model.ocir',compile_source(model_source()))
    jobs=[(k,s) for k in ('native','flat','no_context','no_witness','no_memory','no_invariance') for s in (17,29,43)]
    results=[]
    for kind,seed in jobs:results.append(train_one(kind,seed))
    dump(ROOT/'reports/ALL_TRAINING_RUNS.json',results)
if __name__=='__main__':main()
