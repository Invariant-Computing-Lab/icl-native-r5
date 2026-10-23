"""Replay/control-flow regressions for the independent bytecode backend.

Run: PYTHONPATH=. python -m unittest discover -s tests -p test_vm_replay.py -v
The checkpoint integrity checksum is deliberately NOT an authority mechanism.
"""
import copy
import json
import unittest

from icl.frontend import parse
from icl.runtime import ICLError, digest
from icl.vm import compile_bytecode, execute_bytecode, validate_bytecode


PROGRAMS = [
    ("fn main()->Int64 {return 2+3*4;}", 14),
    ("fn main()->Int64 {var x=0;while x<8 limit 8 {let y=1;x=x+y;}return x;}", 8),
    ("fn f(x:Int64)->Int64 {if x==0 {return 1;}else{return x*f(x-1);}} fn main()->Int64{return f(6);}", 720),
    ("fn main()->Int64 {var x=1;if true {let x=4;}return x;}", 1),
    ("fn main()->Bool {return false && 1/0==2;}", False),
    ("fn main()->Bool {return true || 1/0==2;}", True),
    ("fn main()->Int64 {let a=random_int(100);let b=random_int(100);return a+b;}", 165),
    ("fn main()->Int64 {return -9223372036854775808;}", -(1 << 63)),
    ("fn f(x:Int64)->Int64 {let x=3;return x;} fn main()->Int64 {return f(7);}", 3),
    ("fn main()->Tuple[Int64,String] {let x=(7,\"a\");return x;}", [7, "a"]),
]


def bytecode(source):
    return compile_bytecode(parse("module replay; " + source))


class VMReplayTests(unittest.TestCase):
    def test_every_instruction_boundary_replays_with_identical_state_trace(self):
        for index, (source, expected) in enumerate(PROGRAMS):
            compiled = bytecode(source)
            full = execute_bytecode(compiled)
            with self.subTest(program=index):
                self.assertEqual(full["value"], expected)
                self.assertTrue(all(t["input_hash"] != digest(None) and
                                    t["output_hash"] != digest(None) for t in full["trace"]))
            for cut in range(full["steps"]):
                with self.subTest(program=index, cut=cut):
                    paused = execute_bytecode(compiled, stop_after=cut)
                    checkpoint = json.loads(json.dumps(paused["checkpoint"]))
                    self.assertEqual(execute_bytecode(compiled, checkpoint=checkpoint), full)

    def test_recomputed_checkpoint_checksum_cannot_supply_authority(self):
        compiled = bytecode('fn main()->Bool {return request_effect("journal","entry");}')
        checkpoint = execute_bytecode(compiled, stop_after=0)["checkpoint"]
        checkpoint["policy"] = {"journal": {"allow": True, "human_required": True,
                                               "human_approved": True}}
        checkpoint["integrity"] = digest({k: v for k, v in checkpoint.items() if k != "integrity"})
        with self.assertRaises(ICLError) as raised:
            execute_bytecode(compiled, checkpoint=checkpoint)
        self.assertEqual(raised.exception.code, "CHECKPOINT_CORRUPT")

    def test_authorized_policy_must_be_independently_supplied_on_replay(self):
        compiled = bytecode('fn main()->Bool {return request_effect("journal","entry");}')
        policy = {"journal": {"allow": True}}
        full = execute_bytecode(compiled, policy=policy)
        for cut in range(full["steps"]):
            with self.subTest(cut=cut):
                cp = execute_bytecode(compiled, policy=policy, stop_after=cut)["checkpoint"]
                self.assertEqual(execute_bytecode(compiled, checkpoint=cp, policy=policy), full)
                with self.assertRaises(ICLError):
                    execute_bytecode(compiled, checkpoint=cp)

    def test_bad_opcodes_and_operators_fail_closed(self):
        compiled = bytecode("fn main()->Int64 {return 2+3;}")
        for bad in (None, [], {}, 3, "HOST_EXEC"):
            changed = copy.deepcopy(compiled)
            changed["functions"]["main"]["code"][0]["op"] = bad
            with self.subTest(op=bad), self.assertRaises(ICLError) as raised:
                validate_bytecode(changed)
            self.assertEqual(raised.exception.code, "BYTECODE_CORRUPT")
        for bad in (None, [], {}, "**"):
            changed = copy.deepcopy(compiled)
            next(i for i in changed["functions"]["main"]["code"] if i["op"] == "BINARY")["operator"] = bad
            with self.subTest(operator=bad), self.assertRaises(ICLError):
                execute_bytecode(changed)

    def test_operand_types_are_checked_without_host_exception(self):
        for source in ("fn main()->Int64 {return len(1);}",
                       "fn main()->Int64 {return unwrap(3);}",
                       "fn main()->Int64 {return true;}"):
            with self.subTest(source=source), self.assertRaises(ICLError) as raised:
                execute_bytecode(bytecode(source))
            self.assertEqual(raised.exception.code, "TYPE")
        with self.assertRaises(ICLError):
            execute_bytecode(bytecode("fn main(x:Int64)->Int64{return x;}"), args=[True])

    def test_call_stack_limit_does_not_limit_lexical_scopes(self):
        compiled = bytecode("fn main()->Int64{if true {if true{return 7;}else{return 1;}}else{return 2;}}")
        self.assertEqual(execute_bytecode(compiled, limits={"max_stack": 1})["value"], 7)


if __name__ == "__main__":
    unittest.main()
