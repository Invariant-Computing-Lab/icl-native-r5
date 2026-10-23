"""ICL bytecode compiler and independent stack interpreter.

This backend shares scalar arithmetic, builtins, and resource accounting with
the tree interpreter; it does not call the tree interpreter or execute Python
source. Checkpoint hashes detect accidental modification, not adversarial
forgery: they are unkeyed checksums and confer no trust or authority.
"""
from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy

from .runtime import ICLError, RuntimeContext, builtin, checked_binary, checked_unary, DEFAULT_LIMITS
from .checker import valid_type, validate_value

BYTECODE_SCHEMA = "icl-bytecode/1"
CHECKPOINT_SCHEMA = "icl-vm-checkpoint/1"
OPCODES = {"PUSH", "LOAD", "LET", "STORE", "POP", "BINARY", "UNARY", "CALL",
           "LIST", "TUPLE", "RECORD", "INDEX", "FIELD", "JUMP", "JUMP_FALSE",
           "LOOP_RESET", "LOOP_GUARD", "ENTER_SCOPE", "EXIT_SCOPE", "RETURN"}
_DEFAULT_LIMITS = dict(DEFAULT_LIMITS)


def _fail(code, message, span=None):
    code = {"E_BYTECODE": "BYTECODE_CORRUPT", "E_CHECKPOINT": "CHECKPOINT_CORRUPT",
            "E_LIMIT": "MEMORY_LIMIT", "E_NUMERIC": "NONFINITE", "E_VALUE": "TYPE",
            "E_TYPE": "TYPE", "E_ENTRY": "NAME", "E_NAME": "NAME", "E_ARITY": "TYPE",
            "E_IMMUTABLE": "IMMUTABLE", "E_INDEX": "BOUNDS", "E_FIELD": "TYPE"}.get(code, code)
    raise ICLError(code, message, span)


def _canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        _fail("E_BYTECODE", "Value is not finite canonical JSON")


def _hash(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def compile_bytecode(program):
    """Lower a checked ICL AST to a JSON-serializable instruction stream."""
    functions = {}
    for function in program.get("functions", []):
        name = function["name"]
        if name in functions:
            _fail("E_BYTECODE", "Duplicate function: " + name)
        code = []
        loop_sequence = [0]

        def emit(op, span=None, **kwargs):
            index = len(code)
            code.append({"op": op, **kwargs, "span": span or function.get("span")})
            return index

        def expr(node):
            kind = node["kind"]
            span = node.get("span")
            if kind == "literal":
                emit("PUSH", span, value=node["value"])
            elif kind == "var":
                emit("LOAD", span, name=node["name"])
            elif kind == "binary":
                # Preserve short-circuit evaluation without calling AST eval.
                if node["op"] in ("&&", "and"):
                    expr(node["left"])
                    branch = emit("JUMP_FALSE", span, target=0)
                    expr(node["right"])
                    finish = emit("JUMP", span, target=0)
                    code[branch]["target"] = len(code)
                    emit("PUSH", span, value=False)
                    code[finish]["target"] = len(code)
                elif node["op"] in ("||", "or"):
                    expr(node["left"])
                    branch = emit("JUMP_FALSE", span, target=0)
                    emit("PUSH", span, value=True)
                    finish = emit("JUMP", span, target=0)
                    code[branch]["target"] = len(code)
                    expr(node["right"])
                    code[finish]["target"] = len(code)
                else:
                    expr(node["left"])
                    expr(node["right"])
                    emit("BINARY", span, operator=node["op"])
            elif kind == "unary":
                operand = node["expr"]
                if node["op"] == "-" and operand["kind"] == "literal" and type(operand["value"]) is int and operand["value"] == 1 << 63:
                    emit("PUSH", span, value=-(1 << 63))
                else:
                    expr(operand)
                    emit("UNARY", span, operator=node["op"])
            elif kind == "call":
                for argument in node["args"]:
                    expr(argument)
                emit("CALL", span, name=node["name"], argc=len(node["args"]))
            elif kind in ("list", "tuple"):
                for item in node["items"]:
                    expr(item)
                emit(kind.upper(), span, count=len(node["items"]))
            elif kind == "record":
                ordered_fields = sorted(node["fields"])
                for name in ordered_fields:
                    expr(node["fields"][name])
                emit("RECORD", span, fields=ordered_fields)
            elif kind == "index":
                expr(node["target"])
                expr(node["index"])
                emit("INDEX", span)
            elif kind == "field":
                expr(node["target"])
                emit("FIELD", span, name=node["name"])
            else:
                _fail("E_BYTECODE", "Unsupported expression: " + str(kind), span)

        def statements(nodes, scoped=False):
            if scoped:
                emit("ENTER_SCOPE")
            for node in nodes:
                kind, span = node["kind"], node.get("span")
                if kind == "let":
                    expr(node["expr"])
                    emit("LET", span, name=node["name"], mutable=node.get("mutable", False))
                elif kind == "assign":
                    expr(node["expr"])
                    emit("STORE", span, name=node["name"])
                elif kind == "return":
                    expr(node["expr"]) if node.get("expr") is not None else emit("PUSH", span, value=None)
                    emit("RETURN", span)
                elif kind == "expr":
                    expr(node["expr"])
                    emit("POP", span)
                elif kind == "if":
                    expr(node["cond"])
                    branch = emit("JUMP_FALSE", span, target=0)
                    statements(node["then"], scoped=True)
                    finish = emit("JUMP", span, target=0)
                    code[branch]["target"] = len(code)
                    statements(node.get("else", []), scoped=True)
                    code[finish]["target"] = len(code)
                elif kind == "while":
                    loop_sequence[0] += 1
                    key = str(loop_sequence[0])
                    emit("LOOP_RESET", span, key=key)
                    start = len(code)
                    expr(node["cond"])
                    branch = emit("JUMP_FALSE", span, target=0)
                    emit("LOOP_GUARD", span, key=key, limit=node["limit"])
                    statements(node["body"], scoped=True)
                    emit("JUMP", span, target=start)
                    code[branch]["target"] = len(code)
                else:
                    _fail("E_BYTECODE", "Unsupported statement: " + str(kind), span)
            if scoped:
                emit("EXIT_SCOPE")

        # Parameters occupy the call frame; the function body is a child lexical
        # scope, matching the source rule that a body local may shadow a parameter.
        statements(function["body"], scoped=True)
        emit("PUSH", value=None)
        emit("RETURN")
        functions[name] = {"params": function["params"], "return_type": function["return_type"],
                           "code": code}
    result = {"schema": BYTECODE_SCHEMA, "module": program.get("module", "main"), "functions": functions}
    validate_bytecode(result)
    return result


def _integer(value, lower=0, upper=10000000):
    return type(value) is int and lower <= value <= upper


def _validate_bytecode_impl(bytecode):
    """Fail closed on malformed code before executing any instruction."""
    if not isinstance(bytecode, dict) or bytecode.get("schema") != BYTECODE_SCHEMA:
        _fail("E_BYTECODE", "Unsupported bytecode schema")
    if len(_canonical(bytecode)) > 20000000:
        _fail("E_BYTECODE", "Bytecode exceeds serialized size limit")
    functions = bytecode.get("functions")
    if not isinstance(functions, dict) or not functions or len(functions) > 10000:
        _fail("E_BYTECODE", "Invalid function table")
    for name, function in functions.items():
        if not isinstance(name, str) or not name or not isinstance(function, dict):
            _fail("E_BYTECODE", "Invalid function descriptor")
        params, code = function.get("params"), function.get("code")
        if not isinstance(params, list) or any(not isinstance(p, (list, tuple)) or len(p) != 2
             or not isinstance(p[0], str) or not isinstance(p[1], str) for p in params):
            _fail("E_BYTECODE", "Invalid parameter table")
        if len({p[0] for p in params}) != len(params):
            _fail("E_BYTECODE", "Duplicate parameter")
        if any(not valid_type(p[1]) for p in params) or not isinstance(function.get("return_type"), str) or not valid_type(function["return_type"]):
            _fail("E_BYTECODE", "Invalid function type signature")
        if not isinstance(code, list) or not code or len(code) > 1000000:
            _fail("E_BYTECODE", "Invalid instruction stream")
        for instruction in code:
            if not isinstance(instruction, dict) or not isinstance(instruction.get("op"), str) or instruction["op"] not in OPCODES:
                _fail("E_BYTECODE", "Unknown or malformed opcode")
            op = instruction["op"]
            if op in {"LOAD", "LET", "STORE", "CALL", "FIELD"} and not isinstance(instruction.get("name"), str):
                _fail("E_BYTECODE", "Invalid identifier operand")
            if op == "PUSH" and "value" not in instruction:
                _fail("E_BYTECODE", "Missing literal operand")
            if op == "LET" and type(instruction.get("mutable")) is not bool:
                _fail("E_BYTECODE", "Invalid mutability operand")
            if op in {"LIST", "TUPLE"} and not _integer(instruction.get("count")):
                _fail("E_BYTECODE", "Invalid collection size")
            if op == "CALL" and not _integer(instruction.get("argc")):
                _fail("E_BYTECODE", "Invalid argument count")
            if op == "RECORD" and (not isinstance(instruction.get("fields"), list)
                    or any(not isinstance(k, str) for k in instruction["fields"])
                    or len(instruction["fields"]) != len(set(instruction["fields"]))):
                _fail("E_BYTECODE", "Invalid record fields")
            if op in {"JUMP", "JUMP_FALSE"} and not _integer(instruction.get("target"), 0, len(code) - 1):
                _fail("E_BYTECODE", "Jump target outside instruction stream")
            if op == "BINARY" and (not isinstance(instruction.get("operator"), str) or instruction["operator"] not in {"+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=", "&&", "||"}):
                _fail("E_BYTECODE", "Invalid binary operator")
            if op == "UNARY" and (not isinstance(instruction.get("operator"), str) or instruction["operator"] not in {"-", "!"}):
                _fail("E_BYTECODE", "Invalid unary operator")
            if op in {"LOOP_RESET", "LOOP_GUARD"} and not isinstance(instruction.get("key"), str):
                _fail("E_BYTECODE", "Invalid loop key")
            if op == "LOOP_GUARD" and not _integer(instruction.get("limit"), 0):
                _fail("E_BYTECODE", "Invalid loop limit")
    return True


def validate_bytecode(bytecode):
    """Validate untrusted JSON data and expose only deterministic ICL errors."""
    try:
        return _validate_bytecode_impl(bytecode)
    except ICLError:
        raise
    except (TypeError, KeyError, IndexError, ValueError, AttributeError, RecursionError):
        raise ICLError("BYTECODE_CORRUPT", "Malformed bytecode descriptor") from None


def _normalized_limits(limits):
    result = dict(_DEFAULT_LIMITS)
    if limits:
        for key, value in limits.items():
            if key not in result or not _integer(value, 1, result[key]):
                _fail("RESOURCE_POLICY", "Invalid resource limit: " + str(key))
            result[key] = value
    return result


def _validate_value(value, limits, depth=0, budget=None):
    if budget is None:
        budget = [limits["max_items"]]
    budget[0] -= 1
    if budget[0] < 0 or depth > 128:
        _fail("E_LIMIT", "Value exceeds collection or nesting limit")
    if type(value) is int and not -(1 << 63) <= value < (1 << 63):
        _fail("OVERFLOW", "Int64 overflow")
    if value is None or type(value) in (bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            _fail("E_NUMERIC", "Non-finite floating-point value")
        return
    if isinstance(value, str):
        if len(value) > limits["max_output"]:
            _fail("E_LIMIT", "String exceeds output limit")
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_value(item, limits, depth + 1, budget)
        return
    if isinstance(value, dict) and all(isinstance(k, str) for k in value):
        for item in value.values():
            _validate_value(item, limits, depth + 1, budget)
        return
    _fail("E_VALUE", "Unsupported runtime value")


def _new_frame(name, args, functions, ctx):
    params = functions[name]["params"]
    if len(args) != len(params):
        _fail("E_ARITY", "Wrong argument count for " + name)
    for (_, typ), value in zip(params, args):
        validate_value(value, typ, ctx)
    scope = {"locals": {p[0]: deepcopy(v) for p, v in zip(params, args)},
             "mutable": {p[0]: False for p in params}}
    return {"function": name, "pc": 0, "scopes": [scope], "stack": [], "loops": {}}


def _execute_bytecode(bytecode, entry="main", args=None, limits=None, policy=None,
                     checkpoint=None, stop_after=None):
    """Execute, pause, or resume verified bytecode. No ambient I/O is available."""
    validate_bytecode(bytecode)
    functions = bytecode["functions"]
    limits = _normalized_limits(limits)
    # Authority always comes from this trusted host argument, including replay.
    # A checkpoint is data with an unkeyed checksum, never an authorization token.
    policy = {} if policy is None else policy
    if not isinstance(policy, dict):
        _fail("RESOURCE_POLICY", "Host policy must be an object")
    if stop_after is not None and not _integer(stop_after, 0):
        _fail("E_LIMIT", "stop_after must be a nonnegative integer")
    if checkpoint is not None:
        if not isinstance(checkpoint, dict) or checkpoint.get("schema") != CHECKPOINT_SCHEMA:
            _fail("E_CHECKPOINT", "Unsupported checkpoint schema")
        payload = {k: v for k, v in checkpoint.items() if k != "integrity"}
        if checkpoint.get("integrity") != _hash(payload) or checkpoint.get("bytecode_hash") != _hash(bytecode):
            _fail("E_CHECKPOINT", "Checkpoint integrity or bytecode identity mismatch")
        if len(_canonical(checkpoint)) > 20000000:
            _fail("E_CHECKPOINT", "Checkpoint too large")
        previous_limits = _normalized_limits(checkpoint.get("limits"))
        limits = {k: min(v, previous_limits[k]) for k, v in limits.items()}
        prior_policy = checkpoint.get("policy")
        if policy != prior_policy:
            _fail("E_CHECKPOINT", "Replay requires an independently supplied identical host policy")
    ctx = RuntimeContext(limits=limits, policy=policy)
    if checkpoint is None:
        if entry not in functions:
            _fail("E_ENTRY", "Unknown entry function: " + entry)
        args = [] if args is None else args
        if not isinstance(args, list):
            _fail("E_ARITY", "Entry arguments must be a list")
        _validate_value(args, limits)
        frames = [_new_frame(entry, args, functions, ctx)]
    else:
        frames = deepcopy(checkpoint.get("frames"))
        steps, trace, effects = checkpoint.get("steps"), checkpoint.get("trace"), checkpoint.get("effects")
        if not _integer(steps, 0, limits["max_steps"]) or not isinstance(trace, list) or not isinstance(effects, list):
            _fail("E_CHECKPOINT", "Malformed checkpoint accounting")
        if not isinstance(frames, list) or not frames or len(frames) > limits["max_stack"]:
            _fail("E_CHECKPOINT", "Malformed checkpoint frame stack")
        for frame in frames:
            if not isinstance(frame, dict) or frame.get("function") not in functions:
                _fail("E_CHECKPOINT", "Unknown checkpoint function")
            if not _integer(frame.get("pc"), 0, len(functions[frame["function"]]["code"]) - 1):
                _fail("E_CHECKPOINT", "Invalid checkpoint instruction pointer")
            if not isinstance(frame.get("scopes"), list) or not frame["scopes"] or not isinstance(frame.get("stack"), list):
                _fail("E_CHECKPOINT", "Invalid checkpoint values")
            if len(frame["scopes"]) > limits["max_steps"] + 1:
                _fail("E_CHECKPOINT", "Too many lexical scopes")
            for scope in frame["scopes"]:
                if not isinstance(scope, dict) or not isinstance(scope.get("locals"), dict) or not isinstance(scope.get("mutable"), dict) or set(scope["mutable"]) != set(scope["locals"]) or any(type(v) is not bool for v in scope["mutable"].values()):
                    _fail("E_CHECKPOINT", "Invalid checkpoint mutability table")
                _validate_value(scope["locals"], limits)
            if not isinstance(frame.get("loops"), dict) or any(not _integer(v) for v in frame["loops"].values()):
                _fail("E_CHECKPOINT", "Invalid checkpoint loop counters")
            _validate_value(frame["stack"], limits)
        ctx.steps, ctx.trace, ctx.effects = steps, deepcopy(trace), deepcopy(effects)
        if not _integer(checkpoint.get("prng"), 0, (1 << 31) - 1):
            _fail("E_CHECKPOINT", "Invalid checkpoint PRNG state")
        ctx.prng = checkpoint["prng"]
    start_steps = ctx.steps

    def result(value, paused=False):
        output = {"value": value, "trace": ctx.trace, "effects": ctx.effects,
                  "steps": ctx.steps, "halted": not paused}
        if paused:
            payload = {"schema": CHECKPOINT_SCHEMA, "bytecode_hash": _hash(bytecode),
                       "frames": deepcopy(frames), "steps": ctx.steps, "trace": deepcopy(ctx.trace),
                       "effects": deepcopy(ctx.effects), "limits": limits, "policy": ctx.policy,
                       "prng": ctx.prng}
            payload["integrity"] = _hash(payload)
            output["checkpoint"] = payload
        return output

    while frames:
        if stop_after is not None and ctx.steps - start_steps >= stop_after:
            return result(None, True)
        if len(frames) > limits["max_stack"]:
            _fail("STACK_LIMIT", "VM call stack limit exceeded")
        frame = frames[-1]
        code = functions[frame["function"]]["code"]
        if not 0 <= frame["pc"] < len(code):
            _fail("E_BYTECODE", "Instruction pointer outside function")
        instruction = code[frame["pc"]]
        input_state = {"frames": frames, "prng": ctx.prng}
        trace_index = len(ctx.trace)
        effects_before = len(ctx.effects)
        ctx.step("BC:" + instruction["op"], inputs=input_state)
        frame["pc"] += 1
        op, span, stack = instruction["op"], instruction.get("span"), frame["stack"]

        def finish_trace(return_value=None, returning=False):
            state = {"frames": frames, "prng": ctx.prng}
            if returning:
                state["return_value"] = return_value
            event = ctx.trace[trace_index]
            event["output_hash"] = _hash(state)
            event["state_ref"] = event["output_hash"]
            if len(ctx.effects) > effects_before:
                effect = ctx.effects[-1]
                event["effect_request"] = {"action": effect["action"], "payload_hash": effect["payload_hash"]}
                event["effect_decision"] = effect["decision"]

        def pop(count=1):
            if len(stack) < count:
                _fail("E_BYTECODE", "Operand stack underflow", span)
            if count == 0:
                return []
            values = stack[-count:]
            del stack[-count:]
            return values

        if op == "PUSH":
            stack.append(deepcopy(instruction["value"]))
        elif op == "LOAD":
            name = instruction["name"]
            scope = next((s for s in reversed(frame["scopes"]) if name in s["locals"]), None)
            if scope is None:
                _fail("E_NAME", "Undefined variable: " + name, span)
            stack.append(deepcopy(scope["locals"][name]))
        elif op == "LET":
            name = instruction["name"]
            scope = frame["scopes"][-1]
            if name in scope["locals"]:
                _fail("E_NAME", "Duplicate local declaration: " + name, span)
            scope["locals"][name] = pop()[0]
            scope["mutable"][name] = instruction["mutable"]
        elif op == "STORE":
            name = instruction["name"]
            scope = next((s for s in reversed(frame["scopes"]) if name in s["locals"]), None)
            if scope is None:
                _fail("E_NAME", "Undefined variable: " + name, span)
            if not scope["mutable"][name]:
                _fail("E_IMMUTABLE", "Cannot assign immutable variable: " + name, span)
            scope["locals"][name] = pop()[0]
        elif op == "ENTER_SCOPE":
            frame["scopes"].append({"locals": {}, "mutable": {}})
        elif op == "EXIT_SCOPE":
            if len(frame["scopes"]) <= 1:
                _fail("E_BYTECODE", "Cannot exit function root scope", span)
            frame["scopes"].pop()
        elif op == "POP":
            pop()
        elif op == "BINARY":
            a, b = pop(2)
            stack.append(checked_binary(instruction["operator"], a, b))
        elif op == "UNARY":
            stack.append(checked_unary(instruction["operator"], pop()[0]))
        elif op == "CALL":
            arguments = pop(instruction["argc"])
            name = instruction["name"]
            if name in functions:
                if len(frames) >= limits["max_stack"]:
                    _fail("STACK_LIMIT", "VM call stack limit exceeded", span)
                frames.append(_new_frame(name, arguments, functions, ctx))
            else:
                stack.append(builtin(name, arguments, ctx))
        elif op in {"LIST", "TUPLE"}:
            values = pop(instruction["count"])
            stack.append(values)
        elif op == "RECORD":
            stack.append(dict(zip(instruction["fields"], pop(len(instruction["fields"])))))
        elif op == "INDEX":
            target, index = pop(2)
            if not isinstance(target, (list, tuple, str)) or type(index) is not int or not 0 <= index < len(target):
                _fail("E_INDEX", "Invalid or out-of-range index", span)
            stack.append(target[index])
        elif op == "FIELD":
            target = pop()[0]
            if not isinstance(target, dict) or instruction["name"] not in target:
                _fail("E_FIELD", "Missing record field: " + instruction["name"], span)
            stack.append(target[instruction["name"]])
        elif op == "JUMP":
            frame["pc"] = instruction["target"]
        elif op == "JUMP_FALSE":
            condition = pop()[0]
            if type(condition) is not bool:
                _fail("E_TYPE", "Branch condition must be Bool", span)
            if not condition:
                frame["pc"] = instruction["target"]
        elif op == "LOOP_RESET":
            frame["loops"][instruction["key"]] = 0
        elif op == "LOOP_GUARD":
            key = instruction["key"]
            if key not in frame["loops"]:
                _fail("E_BYTECODE", "Loop guard without reset", span)
            frame["loops"][key] += 1
            if frame["loops"][key] > instruction["limit"]:
                _fail("LOOP_LIMIT", "Bounded loop limit exceeded", span)
        elif op == "RETURN":
            value = pop()[0]
            validate_value(value, functions[frame["function"]]["return_type"], ctx)
            if stack:
                _fail("E_BYTECODE", "Unbalanced operand stack at return", span)
            frames.pop()
            if not frames:
                _validate_value(value, limits)
                finish_trace(value, returning=True)
                return result(value)
            frames[-1]["stack"].append(value)
        if len(stack) > limits["max_items"]:
            _fail("E_LIMIT", "VM operand stack limit exceeded", span)
        if stack:
            _validate_value(stack[-1], limits)
            ctx.check_value(stack[-1])
        finish_trace()
    _fail("E_BYTECODE", "VM terminated without return")


def execute_bytecode(bytecode, entry="main", args=None, limits=None, policy=None,
                     checkpoint=None, stop_after=None):
    """Public fail-closed boundary; malformed data cannot escape as host errors."""
    try:
        return _execute_bytecode(bytecode, entry, args, limits, policy, checkpoint, stop_after)
    except ICLError:
        raise
    except (TypeError, KeyError, IndexError, ValueError, OverflowError, ZeroDivisionError, AttributeError) as error:
        raise ICLError("TYPE", "Malformed bytecode operand or primitive argument: " + type(error).__name__) from None
    except RecursionError:
        raise ICLError("STACK_LIMIT", "Bytecode structure exceeds host recursion limit") from None
