module fixture;
fn inc(x: Int64) -> Int64 { return x + 1; } fn main() -> Int64 { return inc(inc(3)); }
