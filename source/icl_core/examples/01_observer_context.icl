module observer_demo;
fn main() -> Int64 {
  let left = represent(12, "left", "world", "mm");
  let right = represent(7, "left", "world", "mm");
  return repr_value(repr_add(left, right));
}
