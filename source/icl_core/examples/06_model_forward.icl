module tiny_model;
fn main() -> Tensor[1,2] {
  let x = tensor([1.0, -2.0], [1,2]);
  let w = tensor([0.5, 0.2, -0.1, 0.3], [2,2]);
  let b = tensor([0.0, 0.1], [1,2]);
  return softmax(tanh(add(matmul(x, w), b)));
}
