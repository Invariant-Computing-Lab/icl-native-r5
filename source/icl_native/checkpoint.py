"""Safe, explicit tensor/JSON checkpoints. Hash is integrity, not authenticity."""
from __future__ import annotations
import json,os,copy,zipfile,math
from pathlib import Path
import numpy as np
import torch
from safetensors.torch import save_file,load_file
from .common import *
from .graph import model_for,model_source
from icl.api import SCHEMA_SHA256,SCHEMA_VERSION

def save_checkpoint(path:Path,model,optimizer,kind,seed,epoch,step,gen):
    path.mkdir(parents=True,exist_ok=True)
    tmp=path/'weights.safetensors.tmp';save_file({k:v.detach().cpu().contiguous() for k,v in model.state_dict().items()},str(tmp));os.replace(tmp,path/'weights.safetensors')
    tensors={}
    for i,p in enumerate(model.parameters()):
        for k,v in optimizer.state[p].items():
            if not isinstance(v,torch.Tensor):raise TypeError('OPTIMIZER_NON_TENSOR')
            tensors[f'p{i}_{k}']=v.detach().cpu().numpy()
    np.savez_compressed(path/'optimizer.npz',**tensors)
    meta={'kind':kind,'seed':seed,'epoch':epoch,'step':step,'schema_version':SCHEMA_VERSION,'schema_sha256':SCHEMA_SHA256,'graph_source_sha256':hashlib.sha256(model_source().encode()).hexdigest(),'feature_names':FEATURE_NAMES,'actions':ACTIONS,'parameter_count':sum(p.numel() for p in model.parameters()),'global_rng':torch.get_rng_state().tolist(),'batch_rng':gen.get_state().tolist(),'optimizer':'Adam','optimizer_options':{k:v for k,v in optimizer.param_groups[0].items() if k!='params'},'scope':'bounded learned action model; graph emitter/controller/executor external'}
    dump(path/'state.json',meta)
    manifest={'schema':'ICL_R5_CHECKPOINT/1','files':{n:{'sha256':sha(path/n),'bytes':(path/n).stat().st_size} for n in ('weights.safetensors','optimizer.npz','state.json')}}
    dump(path/'manifest.json',manifest)

def load_checkpoint(path:Path,with_optimizer=False):
    if not path.is_dir():raise ValueError('MODEL_NOT_LOADED')
    man=strict_load(path/'manifest.json');expected={'weights.safetensors','optimizer.npz','state.json'}
    if man.get('schema')!='ICL_R5_CHECKPOINT/1' or set(man.get('files',{}))!=expected:raise ValueError('CHECKPOINT_MANIFEST_SCHEMA')
    for n,m in man['files'].items():
        p=path/n
        if p.is_symlink() or not p.is_file() or p.stat().st_size>16_000_000 or p.stat().st_size!=m['bytes'] or sha(p)!=m['sha256']:raise ValueError('CHECKPOINT_INTEGRITY')
    meta=strict_load(path/'state.json')
    if meta['schema_sha256']!=SCHEMA_SHA256 or meta['schema_version']!=SCHEMA_VERSION:raise ValueError('SCHEMA_INCOMPATIBLE')
    if meta['feature_names']!=FEATURE_NAMES or meta['actions']!=ACTIONS or meta['graph_source_sha256']!=hashlib.sha256(model_source().encode()).hexdigest():raise ValueError('MODEL_CONTRACT_INCOMPATIBLE')
    if meta['kind'] not in ('native','flat','no_context','no_witness','no_memory','no_invariance'):raise ValueError('MODEL_KIND')
    model=model_for(meta['kind']);state=load_file(str(path/'weights.safetensors'),device='cpu');ref=model.state_dict()
    if set(state)!=set(ref):raise ValueError('WEIGHT_KEYS')
    if any(state[k].shape!=ref[k].shape or state[k].dtype!=ref[k].dtype or not torch.isfinite(state[k]).all() for k in ref):raise ValueError('WEIGHT_SHAPE_DTYPE_FINITE')
    model.load_state_dict(state,strict=True);model.eval()
    if meta['parameter_count']!=sum(p.numel() for p in model.parameters()):raise ValueError('PARAMETER_COUNT_MISMATCH')
    if not with_optimizer:return model,meta
    with zipfile.ZipFile(path/'optimizer.npz') as arc:
        infos=arc.infolist();names=[z.filename for z in infos];required={f'p{i}_{k}.npy' for i,_ in enumerate(model.parameters()) for k in ('step','exp_avg','exp_avg_sq')}
        if len(names)!=len(set(names)) or set(names)!=required or sum(z.file_size for z in infos)>16_000_000 or any(z.file_size>4_000_000 or z.flag_bits&1 for z in infos):raise ValueError('OPTIMIZER_ARCHIVE_LIMIT_OR_SCHEMA')
    if meta['optimizer']!='Adam':raise ValueError('OPTIMIZER_KIND')
    opts=meta['optimizer_options'];optimizer=torch.optim.Adam(model.parameters(),lr=opts['lr'],betas=tuple(opts['betas']),eps=opts['eps'],weight_decay=opts['weight_decay'])
    with np.load(path/'optimizer.npz',allow_pickle=False) as z:
        for i,p in enumerate(model.parameters()):
            for k in ('step','exp_avg','exp_avg_sq'):
                arr=z[f'p{i}_{k}'];val=torch.from_numpy(np.array(arr,copy=True))
                if k!='step' and val.shape!=p.shape:raise ValueError('OPTIMIZER_SHAPE')
                if not torch.isfinite(val).all():raise ValueError('OPTIMIZER_NONFINITE')
                optimizer.state[p][k]=val
    torch.set_rng_state(torch.tensor(meta['global_rng'],dtype=torch.uint8));gen=torch.Generator();gen.set_state(torch.tensor(meta['batch_rng'],dtype=torch.uint8))
    return model,meta,optimizer,gen
