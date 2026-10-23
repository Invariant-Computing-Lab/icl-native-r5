module fixture;
fn main() -> Tensor[1,1] { return matmul(tensor([1.0, 2.0], [1,2]), tensor([3.0, 4.0], [2,1])); }
