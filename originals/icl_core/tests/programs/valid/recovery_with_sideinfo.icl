module fixture;
fn main() -> Int64 { let y = observe_mod(257, 256, "mod_sensor"); let w = make_witness(257, 256); return exact_value(recover(y, w)); }
