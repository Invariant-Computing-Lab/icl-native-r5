module fixture;
fn main() -> Int64 { let forged = {tag: "RecoveryWitness", quotient: 1}; return exact_value(recover(observe_mod(1,256,"o"),forged)); }
