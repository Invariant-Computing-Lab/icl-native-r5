module checkpoint;
fn main() -> Int64 {
  var i = 0;
  var total = 0;
  while i < 8 limit 8 { total = total + random_int(100); i = i + 1; }
  return total;
}
