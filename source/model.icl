module model_graph;
fn main(x:Tensor[1,30],w1:Tensor[30,32],b1:Tensor[1,32],w2:Tensor[32,32],b2:Tensor[1,32],wo:Tensor[32,22],bo:Tensor[1,22])->Tensor[1,22] {
let h1=tanh(add(matmul(x,w1),b1));
let h2=tanh(add(matmul(h1,w2),b2));
return add(matmul(h2,wo),bo);
}
