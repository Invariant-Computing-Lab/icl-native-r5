"""Trainable PyTorch execution of a compiled, type-checked ICL tensor graph.
Batching is a mapped application of the declared single-row graph. All bias
broadcasting is that mapped application, not a change to ICL's shape semantics.
"""
from __future__ import annotations
import sys
from pathlib import Path
import torch
from torch import nn
from .common import ROOT,D,K,H,digest
sys.path.insert(0,str(ROOT/'source/icl_core'))
from icl.api import compile_source,validate_ocir
OPS={'matmul':lambda a,b:a@b,'add':lambda a,b:a+b,'sub':lambda a,b:a-b,'mul':lambda a,b:a*b,'tanh':torch.tanh,'relu':torch.relu,'softmax':lambda x:torch.softmax(x,dim=-1)}

def model_source()->str:
    return f'''module model_graph;
fn main(x:Tensor[1,{D}],w1:Tensor[{D},{H}],b1:Tensor[1,{H}],w2:Tensor[{H},{H}],b2:Tensor[1,{H}],wo:Tensor[{H},{K}],bo:Tensor[1,{K}])->Tensor[1,{K}] {{
let h1=tanh(add(matmul(x,w1),b1));
let h2=tanh(add(matmul(h1,w2),b2));
return add(matmul(h2,wo),bo);
}}
'''

def graph_call(ocir:dict,env:dict[str,torch.Tensor])->torch.Tensor:
    fn=ocir['typed_blocks'][0]
    def e(n):
        if n['kind']=='var':return env[n['name']]
        if n['kind']=='call' and n['name'] in OPS:return OPS[n['name']](*[e(a) for a in n['args']])
        raise ValueError('UNSUPPORTED_GRAPH_NODE')
    for node in fn['body']:
        if node['kind']=='let':env[node['name']]=e(node['expr'])
        elif node['kind']=='return':return e(node['expr'])
        else:raise ValueError('UNSUPPORTED_GRAPH_STATEMENT')
    raise ValueError('GRAPH_MISSING_RETURN')

class Native(nn.Module):
    def __init__(self):
        super().__init__();self.graph=compile_source(model_source());validate_ocir(self.graph)
        self.w1=nn.Parameter(torch.randn(D,H)*.1);self.b1=nn.Parameter(torch.zeros(1,H))
        self.w2=nn.Parameter(torch.randn(H,H)*.1);self.b2=nn.Parameter(torch.zeros(1,H))
        self.wo=nn.Parameter(torch.randn(H,K)*.1);self.bo=nn.Parameter(torch.zeros(1,K))
    def forward(self,x):
        if x.ndim!=2 or x.shape[-1]!=D:raise ValueError('MODEL_INPUT_SHAPE')
        return graph_call(self.graph,{'x':x,**dict(self.named_parameters())})

class FlatTokens(nn.Module):
    """Matched-count flattened-token baseline. Field-qualified tokens retain flags.
    Six numeric values are discretized; therefore quality/compute parity is
    explicitly reported, not assumed equivalent information precision.
    """
    V=16+16+6*9
    def __init__(self):
        super().__init__();target=sum(p.numel() for p in Native().parameters())
        width=min(range(16,65),key=lambda h:abs(self.V*8+8*h+h+h*32+32+32*K+K-target))
        self.embedding=nn.Embedding(self.V,8);self.l1=nn.Linear(8,width);self.l2=nn.Linear(width,32);self.out=nn.Linear(32,K)
    def forward(self,x):
        intent=x[:,:16].argmax(-1)[:,None]
        flags=(x[:,16:24]>.5).long()+torch.arange(8,device=x.device)[None,:]*2+16
        numbers=((x[:,24:]+1)*4).round().long().clamp(0,8)+torch.arange(6,device=x.device)[None,:]*9+32
        tokens=torch.cat([intent,flags,numbers],1)
        emb=self.embedding(tokens).mean(1)
        return self.out(torch.tanh(self.l2(torch.tanh(self.l1(emb)))))

def model_for(kind:str):return FlatTokens() if kind=='flat' else Native()
