"""Deterministic program generators spanning distinct control/data families.

The generator writes the seed, exact source, arguments, expected host result and
both engine outputs to the evidence JSONL. It does not count repeated invocations
of one arithmetic expression as new semantic coverage.
"""
import random
from cases import Case

SEED=0x1C1C0DE

def _generate(count):
    rng=random.Random(SEED)
    for i in range(count):
        a,b,c=[rng.randrange(-30,31) for _ in range(3)]
        n=rng.randrange(0,12)
        family=i % 12
        if family==0:
            src=f'fn main() -> Int64 {{ return ({a} + {b}) * {c}; }}'
            expected=(a+b)*c; label='integer_expression'
        elif family==1:
            src=f'fn main(x: Int64) -> Int64 {{ if x < {b} {{ return x + {c}; }} else {{ return x - {c}; }} }}'
            expected=a+c if a<b else a-c; label='conditional_parameter'
        elif family==2:
            src=f'fn main() -> Int64 {{ var i: Int64 = 0; var s: Int64 = {a}; while i < {n} limit 20 {{ s = s + i * {b}; i = i + 1; }} return s; }}'
            expected=a+b*n*(n-1)//2; label='bounded_loop'
        elif family==3:
            src=f'fn f(x: Int64) -> Int64 {{ return x * {b} + {c}; }} fn main() -> Int64 {{ return f(f({a})); }}'
            expected=(a*b+c)*b+c; label='function_composition'
        elif family==4:
            src=f'fn main() -> Int64 {{ let xs = [{a}, {b}, {c}]; return xs[{n%3}] + len(xs); }}'
            expected=[a,b,c][n%3]+3; label='list_index_length'
        elif family==5:
            src=f'fn main() -> Int64 {{ let r = {{left: {a}, right: {b}}}; return r.left * {c} + r.right; }}'
            expected=a*c+b; label='record_projection'
        elif family==6:
            src=f'fn main() -> Int64 {{ let t = ({a}, {b}, {c}); return t[{n%3}]; }}'
            expected=[a,b,c][n%3]; label='tuple_projection'
        elif family==7:
            src=f'fn main() -> Bool {{ return ({a} < {b}) && ({b} != {c}) || ({a} == {c}); }}'
            expected=(a<b and b!=c) or a==c; label='boolean_precedence'
        elif family==8:
            src=f'fn main() -> Float64 {{ return ({a}.0 + {b}.0) / {n+1}.0; }}'
            expected=(a+b)/(n+1); label='float_division'
        elif family==9:
            src=f'fn main() -> Int64 {{ var x: Int64 = {a}; if {b} >= 0 {{ x = x + {b}; }} else {{ x = x - {b}; }} if x > {c} {{ return x; }} else {{ return {c}; }} }}'
            expected=max(a+abs(b),c); label='branch_mutation'
        elif family==10:
            m=n%6
            src=f'fn recsum(n: Int64) -> Int64 {{ if n == 0 {{ return {a}; }} else {{ return n + recsum(n - 1); }} }} fn main() -> Int64 {{ return recsum({m}); }}'
            expected=a+m*(m+1)//2; label='recursive_function'
        else:
            src=f'fn choose(a: Int64, b: Int64) -> Int64 {{ if a < b {{ return b; }} else {{ return a; }} }} fn main() -> Int64 {{ let r = {{x: {a}, y: {b}}}; return choose(r.x, r.y) + {c}; }}'
            expected=max(a,b)+c; label='mixed_record_call'
        yield Case(f'generated_{i:04d}_{label}',label,src,expected,args=[a] if family==1 else [])


def generate(count=1008):
    """Emit count genuinely distinct source/argument pairs from the seeded stream."""
    import json
    seen=set()
    emitted=0
    for case in _generate(count*3):
        identity=(case.source,json.dumps(case.args,sort_keys=True))
        if identity in seen:continue
        seen.add(identity)
        yield case
        emitted+=1
        if emitted==count:return
    raise RuntimeError("seeded generation failed to provide requested unique cases")
