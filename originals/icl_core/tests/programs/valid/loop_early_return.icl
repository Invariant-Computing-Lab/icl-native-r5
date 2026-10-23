module fixture;
fn main() -> Int64 { var i: Int64 = 0; while i < 10 limit 12 { if i == 4 { return i; } i = i + 1; } return 0; }
