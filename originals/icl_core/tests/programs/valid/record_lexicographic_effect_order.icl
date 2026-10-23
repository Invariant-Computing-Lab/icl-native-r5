module fixture;
fn main() -> List[Int64] { let r = {z: random_int(100), a: random_int(100)}; return [r.z,r.a]; }
