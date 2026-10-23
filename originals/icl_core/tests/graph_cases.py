"""Eight independent NumPy reference forward graphs. No VM builtins used in oracle."""
import json
import numpy as np
from cases import Case

def lit(a):
    a=np.asarray(a,dtype=np.float64)
    return 'tensor('+json.dumps(a.ravel().tolist())+', '+json.dumps(list(a.shape))+')'

def normalize(a):
    return (a-a.mean(axis=-1,keepdims=True))/np.sqrt(a.var(axis=-1,keepdims=True)+1e-5)

def softmax(a):
    e=np.exp(a-a.max(axis=-1,keepdims=True));return e/e.sum(axis=-1,keepdims=True)

def graph_cases():
    rng=np.random.default_rng(412071)
    x=rng.normal(size=(2,3));w=rng.normal(size=(3,4));b=rng.normal(size=(2,4));w2=rng.normal(size=(4,2));b2=rng.normal(size=(2,2))
    x1=rng.normal(size=(3,2));w1=rng.normal(size=(2,3));r=rng.normal(size=(3,3))
    entries=[
        ('affine_matmul_add',f'add(matmul({lit(x)}, {lit(w)}), {lit(b)})',x@w+b),
        ('relu_matmul',f'relu(matmul({lit(x)}, {lit(w)}))',np.maximum(x@w,0)),
        ('tanh_matmul',f'tanh(matmul({lit(x1)}, {lit(w1)}))',np.tanh(x1@w1)),
        ('reshape_add',f'add(reshape({lit(x1)}, [2,3]), {lit(x)})',x1.reshape(2,3)+x),
        ('row_normalization',f'normalize({lit(r)})',normalize(r)),
        ('softmax_logits',f'softmax(matmul({lit(x1)}, {lit(w1)}))',softmax(x1@w1)),
        ('two_layer_mlp',f'add(matmul(tanh(add(matmul({lit(x)}, {lit(w)}), {lit(b)})), {lit(w2)}), {lit(b2)})',np.tanh(x@w+b)@w2+b2),
        ('residual_norm_softmax',f'softmax(normalize(add(matmul({lit(x1)}, {lit(w1)}), {lit(r)})))',softmax(normalize(x1@w1+r))),
    ]
    for name,expr,expected in entries:
        dims=','.join(map(str,expected.shape));src=f'module graph; fn main() -> Tensor[{dims}] {{ return {expr}; }}'
        yield Case('numpy_'+name,'numpy_forward',src,{'shape':list(expected.shape),'data':expected.ravel().tolist()})
