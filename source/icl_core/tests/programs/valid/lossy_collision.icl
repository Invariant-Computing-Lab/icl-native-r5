module fixture;
fn main() -> Bool { return repr_value(observe_mod(1, 256, "mod_sensor")) == repr_value(observe_mod(257, 256, "mod_sensor")); }
