module frames;
fn main() -> Float64 {
  let local = represent(3.5, "camera", "camera_frame", "mm");
  let world = convert_frame(local, "world", 10.0, "affine_translation_v1");
  return repr_value(world);
}
