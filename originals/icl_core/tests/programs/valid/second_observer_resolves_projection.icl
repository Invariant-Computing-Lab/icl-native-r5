module fixture;
fn main() -> Bool { let h = tensor([0.0, 1.0], [2,1]); let a = tensor([2.0, 7.0], [1,2]); let b = tensor([2.0, 9.0], [1,2]); return matmul(a, h) != matmul(b, h); }
