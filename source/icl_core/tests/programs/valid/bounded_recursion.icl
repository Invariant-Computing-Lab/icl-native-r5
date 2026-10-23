module fixture;
fn f(n: Int64) -> Int64 { if n <= 1 { return 1; } else { return n * f(n - 1); } } fn main() -> Int64 { return f(5); }
