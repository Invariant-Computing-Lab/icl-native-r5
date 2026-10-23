"""Hand-reviewed conformance fixtures; each tests a distinct language behaviour."""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Case:
    name: str
    family: str
    source: str
    expected: Any = None
    error: str | None = None
    args: list = field(default_factory=list)
    modules: dict = field(default_factory=dict)
    limits: dict | None = None
    policy: dict | None = None

    def __post_init__(self):
        if not self.source.lstrip().startswith("module "):
            self.source = "module fixture;\n" + self.source

CASES = [
 Case('int_identity','scalar','fn main(x: Int64) -> Int64 { return x; }', 17,args=[17]),
 Case('integer_precedence','arithmetic','fn main() -> Int64 { return 2 + 3 * 4; }',14),
 Case('integer_parentheses','arithmetic','fn main() -> Int64 { return (2 + 3) * 4; }',20),
 Case('negative_integer','arithmetic','fn main() -> Int64 { return -8 + 3; }',-5),
 Case('integer_comparison','boolean','fn main() -> Bool { return 9 >= 9; }',True),
 Case('boolean_negation','boolean','fn main() -> Bool { return !false; }',True),
 Case('boolean_conjunction','boolean','fn main() -> Bool { return true && false; }',False),
 Case('boolean_disjunction','boolean','fn main() -> Bool { return false || true; }',True),
 Case('float_arithmetic','float','fn main() -> Float64 { return 0.5 + 1.25; }',1.75),
 Case('float_division','float','fn main() -> Float64 { return 7.5 / 2.5; }',3.0),
 Case('string_identity','string','fn main() -> String { return "OCIL"; }','OCIL'),
 Case('string_unicode_value','string','fn main() -> String { return "gözlemci λ"; }','gözlemci λ'),
 Case('lexical_binding','scope','fn main() -> Int64 { let x = 12; let y = x + 7; return y; }',19),
 Case('mutable_update','scope','fn main() -> Int64 { var x: Int64 = 2; x = x * 3; return x; }',6),
 Case('branch_true','branch','fn main() -> Int64 { if 2 < 3 { return 11; } else { return 22; } }',11),
 Case('branch_false','branch','fn main() -> Int64 { if 2 > 3 { return 11; } else { return 22; } }',22),
 Case('branch_mutation','branch','fn main() -> Int64 { var x: Int64 = 0; if true { x = 6; } else { x = 9; } return x; }',6),
 Case('nested_branch','branch','fn main() -> Int64 { if true { if false { return 1; } else { return 2; } } else { return 3; } }',2),
 Case('loop_sum','loop','fn main() -> Int64 { var i: Int64 = 0; var n: Int64 = 0; while i < 5 limit 8 { n = n + i; i = i + 1; } return n; }',10),
 Case('loop_zero_iterations','loop','fn main() -> Int64 { var n: Int64 = 7; while n < 0 limit 3 { n = n + 1; } return n; }',7),
 Case('loop_early_return','loop','fn main() -> Int64 { var i: Int64 = 0; while i < 10 limit 12 { if i == 4 { return i; } i = i + 1; } return 0; }',4),
 Case('function_call','function','fn twice(x: Int64) -> Int64 { return x * 2; } fn main() -> Int64 { return twice(9); }',18),
 Case('function_composition','function','fn inc(x: Int64) -> Int64 { return x + 1; } fn main() -> Int64 { return inc(inc(3)); }',5),
 Case('two_argument_function','function','fn diff(a: Int64, b: Int64) -> Int64 { return a - b; } fn main() -> Int64 { return diff(9, 2); }',7),
 Case('bounded_recursion','function','fn f(n: Int64) -> Int64 { if n <= 1 { return 1; } else { return n * f(n - 1); } } fn main() -> Int64 { return f(5); }',120),
 Case('list_index','list','fn main() -> Int64 { let xs = [2, 4, 6]; return xs[1]; }',4),
 Case('list_length','list','fn main() -> Int64 { let xs = [2, 4, 6]; return len(xs); }',3),
 Case('tuple_index','tuple','fn main() -> Int64 { let p = (7, "a"); return p[0]; }',7),
 Case('record_field','record','fn main() -> Int64 { let r = {count: 7, label: "ok"}; return r.count; }',7),
 Case('record_nested','record','fn main() -> Int64 { let r = {inner: {count: 8}}; return r.inner.count; }',8),
 Case('undefined_name','name','fn main() -> Int64 { return missing; }',error='NAME'),
 Case('undefined_function','name','fn main() -> Int64 { return missing(1); }',error='NAME'),
 Case('wrong_return_type','type','fn main() -> Int64 { return true; }',error='TYPE'),
 Case('mixed_arithmetic','type','fn main() -> Int64 { return 1 + true; }',error='TYPE'),
 Case('wrong_call_arity','type','fn f(x: Int64) -> Int64 { return x; } fn main() -> Int64 { return f(1, 2); }',error='TYPE'),
 Case('condition_not_boolean','type','fn main() -> Int64 { if 1 { return 1; } else { return 2; } }',error='TYPE'),
 Case('immutable_assignment','type','fn main() -> Int64 { let x = 1; x = 2; return x; }',error='IMMUTABLE'),
 Case('integer_overflow','numeric','fn main() -> Int64 { return 9223372036854775807 + 1; }',error='OVERFLOW'),
 Case('zero_division','numeric','fn main() -> Float64 { return 1.0 / 0.0; }',error='DIVISION_BY_ZERO'),
 Case('list_out_of_bounds','bounds','fn main() -> Int64 { return [1, 2][5]; }',error='BOUNDS'),
 Case('heterogeneous_list','type','fn main() -> Int64 { let xs = [1, true]; return 0; }',error='TYPE'),
 Case('missing_record_field','type','fn main() -> Int64 { let r = {count: 1}; return r.missing; }',error='NAME'),
 Case('missing_semicolon','parse','fn main() -> Int64 { return 1 }',error='PARSE'),
 Case('invalid_lexeme','lex','fn main() -> Int64 { return @; }',error='LEX'),
]

CASES += [
 Case('module_import_call','module','module fixture; import mathlib; fn main() -> Int64 { return mathlib.triple(5); }',15,modules={'mathlib':'module mathlib; fn triple(x: Int64) -> Int64 { return x * 3; }'}),
 Case('option_some','option','fn main() -> Int64 { return unwrap(some(5)); }',5),
 Case('option_none','option','fn main() -> Bool { return is_some(none_int()); }',False),
 Case('result_ok','result','fn main() -> Int64 { return unwrap(ok(8)); }',8),
 Case('result_error','result','fn main() -> Int64 { return unwrap(err_int("unavailable")); }',error='UNWRAP'),
 Case('observer_conditioned_value','observer','fn main() -> Int64 { return repr_value(represent(7, "left", "world", "m")); }',7),
 Case('observer_add_compatible','observer','fn main() -> Int64 { let a = represent(2, "left", "world", "m"); let b = represent(5, "left", "world", "m"); return repr_value(repr_add(a, b)); }',7),
 Case('observer_mismatch','observer','fn main() -> Int64 { let a = represent(2, "left", "world", "m"); let b = represent(5, "right", "world", "m"); return repr_value(repr_add(a, b)); }',error='OBSERVER_MISMATCH'),
 Case('frame_mismatch','observer','fn main() -> Int64 { let a = represent(2, "left", "world", "m"); let b = represent(5, "left", "camera", "m"); return repr_value(repr_add(a, b)); }',error='FRAME_MISMATCH'),
 Case('unit_mismatch','observer','fn main() -> Int64 { let a = represent(2, "left", "world", "m"); let b = represent(5, "left", "world", "cm"); return repr_value(repr_add(a, b)); }',error='UNIT_MISMATCH'),
 Case('explicit_frame_conversion','observer','fn main() -> Int64 { let a = represent(2, "left", "world", "m"); return repr_value(convert_frame(a, "camera", 3, "affine_translation_v1")); }',5),
 Case('out_of_family_transform','observer','fn main() -> Int64 { let a = represent(2, "left", "world", "m"); return repr_value(convert_frame(a, "camera", 3, "nonlinear_unregistered")); }',error='NEEDS_EVIDENCE'),
 Case('lossy_collision','recovery','fn main() -> Bool { return repr_value(observe_mod(1, 256, "mod_sensor")) == repr_value(observe_mod(257, 256, "mod_sensor")); }',True),
 Case('recovery_with_sideinfo','recovery','fn main() -> Int64 { let y = observe_mod(257, 256, "mod_sensor"); let w = make_witness(257, 256); return exact_value(recover(y, w)); }',257),
 Case('non_identifiable_without_witness','recovery','fn main() -> Int64 { let y = observe_mod(257, 256, "mod_sensor"); return exact_value(recover_without_witness(y)); }',error='NON_IDENTIFIABLE'),
 Case('wrong_pairing_witness','recovery','fn main() -> Int64 { let y = observe_mod(257, 256, "mod_sensor"); let w = make_witness(258, 256); return exact_value(recover(y, w)); }',error='WITNESS_CORRUPT'),
 Case('denied_effect','effect','fn main() -> Bool { return request_effect("journal", "entry"); }',error='EFFECT_DENIED'),
 Case('allowed_local_journal','effect','fn main() -> Bool { return request_effect("journal", "entry"); }',True,policy={'journal':{'allow':True}}),
 Case('human_approval_required','effect','fn main() -> Bool { return request_effect("journal", "entry"); }',error='HUMAN_APPROVAL_REQUIRED',policy={'journal':{'allow':True,'human_required':True}}),
 Case('tensor_matmul','tensor','fn main() -> Tensor[1,1] { return matmul(tensor([1.0, 2.0], [1,2]), tensor([3.0, 4.0], [2,1])); }',{'shape':[1,1],'data':[11.0]}),
 Case('tensor_relu','tensor','fn main() -> Tensor[3] { return relu(tensor([-1.0, 0.0, 2.0], [3])); }',{'shape':[3],'data':[0.0,0.0,2.0]}),
 Case('tensor_reshape','tensor','fn main() -> Tensor[2,2] { return reshape(tensor([1.0, 2.0, 3.0, 4.0], [4]), [2,2]); }',{'shape':[2,2],'data':[1.0,2.0,3.0,4.0]}),
 Case('tensor_shape_invalid','tensor','fn main() -> Tensor[2] { return tensor([1.0], [2]); }',error='SHAPE'),
 Case('approximation_explicit','approx','fn main() -> Float64 { return approx_value(approx(0.5, 0.1)); }',0.5),
]
CASES += [
 Case('int64_minimum','numeric','fn main() -> Int64 { return -9223372036854775808; }',-(1<<63)),
 Case('short_circuit_and','boolean','fn main() -> Bool { return false && (1 / 0 == 1); }',False),
 Case('short_circuit_or','boolean','fn main() -> Bool { return true || (1 / 0 == 1); }',True),
 Case('branch_scope_shadow','scope','fn main() -> Int64 { let x = 7; if true { let x = 8; } return x; }',7),
 Case('branch_scope_does_not_escape','scope','fn main() -> Int64 { if true { let x = 8; } return x; }',error='NAME'),
]
CASES += [
 Case('rank_deficient_projection_collision','identifiability','fn main() -> Bool { let h = tensor([1.0, 0.0], [2,1]); let a = tensor([2.0, 7.0], [1,2]); let b = tensor([2.0, 9.0], [1,2]); return matmul(a, h) == matmul(b, h); }',True),
 Case('second_observer_resolves_projection','identifiability','fn main() -> Bool { let h = tensor([0.0, 1.0], [2,1]); let a = tensor([2.0, 7.0], [1,2]); let b = tensor([2.0, 9.0], [1,2]); return matmul(a, h) != matmul(b, h); }',True),
]
CASES += [
 Case('parameter_shadow_in_body','scope','fn f(x: Int64) -> Int64 { let x = 3; return x; } fn main() -> Int64 { return f(9); }',3),
]
CASES += [
 Case('record_lexicographic_effect_order','record','fn main() -> List[Int64] { let r = {z: random_int(100), a: random_int(100)}; return [r.z,r.a]; }',[75,90]),
]
