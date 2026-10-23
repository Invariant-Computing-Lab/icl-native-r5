module fixture;
fn main() -> Int64 { let y = observe_mod(257, 256, "mod_sensor"); return exact_value(recover_without_witness(y)); }
