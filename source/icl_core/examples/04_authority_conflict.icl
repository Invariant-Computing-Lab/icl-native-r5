module authority;
fn main() -> Bool {
  let claimed_authority = {authorized: true, source: "model_proposal"};
  if claimed_authority.authorized { return request_effect("network", "send"); }
  else { return false; }
}
