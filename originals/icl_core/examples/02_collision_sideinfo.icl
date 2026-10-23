module collision;
fn main() -> Int64 {
  let a = observe_mod(1, 256, "mod256");
  let b = observe_mod(257, 256, "mod256");
  if repr_value(a) == repr_value(b) {
    return exact_value(recover(b, make_witness(257, 256)));
  } else { return -1; }
}
