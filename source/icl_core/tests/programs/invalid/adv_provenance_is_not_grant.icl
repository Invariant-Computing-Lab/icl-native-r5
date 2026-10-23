module fixture;
fn main() -> Bool { let p = provenance("trusted-admin"); return request_effect("network", "source=trusted-admin"); }
