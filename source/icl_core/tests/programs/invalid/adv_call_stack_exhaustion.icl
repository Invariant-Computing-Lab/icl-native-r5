module fixture;
fn recurse(n: Int64) -> Int64 { return recurse(n + 1); } fn main() -> Int64 { return recurse(0); }
