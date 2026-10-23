module rank_deficient;
fn main() -> Bool {
  let h = tensor([1.0, 0.0], [1,2]);
  let x1 = tensor([1.0, 2.0], [2,1]);
  let x2 = tensor([1.0, 9.0], [2,1]);
  return sum(matmul(h,x1)) == sum(matmul(h,x2));
}
