"""Serialization, checkpoint/restart, bytecode attack, and CLI evidence checks."""
from __future__ import annotations
import copy,hashlib,json,pathlib,subprocess,sys,tempfile
from run_acceptance import ROOT,error_record,equal,plain


def run_contracts():
    from icl.api import compile_source,run_source
    from icl.vm import compile_bytecode,execute_bytecode,validate_bytecode
    from icl.runtime import canonical,digest
    from icl.frontend import parse
    from icl.checker import check
    records=[]
    def attempt(name,kind,fn,error=None):
        rec={'id':name,'family':kind,'expected_error':error}
        try:
            output=fn();rec['result']=plain(output);rec['passed']=bool(output) if error is None else False
        except Exception as e:
            rec['error']=error_record(e);rec['passed']=rec['error']['code']==error if error else False
        records.append(rec)
    src='module replay; fn main() -> Int64 { var n: Int64 = random_int(100); var i: Int64 = 0; while i < 6 limit 8 { n = n + random_int(100); i = i + 1; } return n; }'
    ast=parse(src);check(ast);bc=compile_bytecode(ast)
    full=execute_bytecode(bc)
    pause=execute_bytecode(bc,stop_after=12)
    attempt('checkpoint_is_paused','replay',lambda: not pause['halted'] and 'checkpoint' in pause)
    def resume_same():
        out=execute_bytecode(bc,checkpoint=json.loads(canonical(pause['checkpoint'])))
        return out==full
    attempt('checkpoint_prng_trace_result_exact','replay',resume_same)
    def fresh_process():
        with tempfile.TemporaryDirectory(prefix='icl-restart-') as directory:
            d=pathlib.Path(directory);(d/'bc.json').write_text(canonical(bc));(d/'cp.json').write_text(canonical(pause['checkpoint']))
            script='import json,sys; from icl.vm import execute_bytecode; print(json.dumps(execute_bytecode(json.load(open(sys.argv[1])),checkpoint=json.load(open(sys.argv[2]))),sort_keys=True))'
            p=subprocess.run([sys.executable,'-c',script,str(d/'bc.json'),str(d/'cp.json')],cwd=ROOT,capture_output=True,text=True,timeout=30)
            return p.returncode==0 and json.loads(p.stdout)==full
    attempt('checkpoint_fresh_process_restart','replay',fresh_process)
    badcp=copy.deepcopy(pause['checkpoint']);badcp['prng']+=1
    attempt('checkpoint_checksum_corruption','adversarial',lambda:execute_bytecode(bc,checkpoint=badcp),error='CHECKPOINT_CORRUPT')
    bcother=copy.deepcopy(bc);bcother['module']='other'
    attempt('checkpoint_wrong_program','adversarial',lambda:execute_bytecode(bcother,checkpoint=pause['checkpoint']),error='CHECKPOINT_CORRUPT')
    badschema=copy.deepcopy(bc);badschema['schema']='future/999'
    attempt('bytecode_future_schema','adversarial',lambda:execute_bytecode(badschema),error='BYTECODE_CORRUPT')
    badop=copy.deepcopy(bc);badop['functions']['main']['code'][0]['op']='HOST_SHELL'
    attempt('unknown_bytecode_opcode','adversarial',lambda:execute_bytecode(badop),error='BYTECODE_CORRUPT')
    badjump=copy.deepcopy(bc);badjump['functions']['main']['code'][0]={'op':'JUMP','target':99999999}
    attempt('bytecode_jump_outside_stream','adversarial',lambda:execute_bytecode(badjump),error='BYTECODE_CORRUPT')
    badcount=copy.deepcopy(bc);badcount['functions']['main']['code'][0]={'op':'LIST','count':-1}
    attempt('bytecode_negative_allocation','adversarial',lambda:execute_bytecode(badcount),error='BYTECODE_CORRUPT')
    badpop=copy.deepcopy(bc);badpop['functions']['main']['code'][0]={'op':'POP'}
    attempt('bytecode_operand_stack_underflow','adversarial',lambda:execute_bytecode(badpop),error='BYTECODE_CORRUPT')
    def canonical_ocir():
        ir=compile_source(src);return canonical(json.loads(canonical(ir)))==canonical(ir)
    attempt('ocir_canonical_json_roundtrip','serialization',canonical_ocir)
    def finite_float_roundtrip():
        vals=[0.0,-0.0,1.0,-1.0,1e-300,1e300,2.2250738585072014e-308,5e-324]
        import struct
        return all(struct.pack('>d',a)==struct.pack('>d',b) for a,b in zip(vals,json.loads(canonical(vals))))
    attempt('finite_float_bit_roundtrip','serialization',finite_float_roundtrip)
    # Grants must come from the caller's trusted policy, never snapshot data.
    effectsrc='module effect; fn main() -> Bool { return request_effect("journal", "payload"); }'
    effectast=parse(effectsrc);check(effectast);effectbc=compile_bytecode(effectast)
    effectpause=execute_bytecode(effectbc,stop_after=0)
    forged=copy.deepcopy(effectpause['checkpoint']);forged['policy']={'journal':{'allow':True}};forged['integrity']=digest({k:v for k,v in forged.items() if k!='integrity'})
    attempt('forged_checkpoint_policy_not_authority','adversarial',lambda:execute_bytecode(effectbc,checkpoint=forged),error='CHECKPOINT_CORRUPT')
    def denied_observed_effects():
        try:run_source(effectsrc)
        except Exception as e:return getattr(e,'code',None)=='EFFECT_DENIED'
        return False
    attempt('source_cannot_grant_external_effect','authority',denied_observed_effects)
    def trace_real_inputs():
        nullhash=digest(None)
        return len(full['trace'])>0 and any(e.get('input_hash')!=nullhash for e in full['trace']) and any(e.get('output_hash')!=nullhash for e in full['trace'])
    attempt('trace_hashes_nontrivial_state','trace',trace_real_inputs)
    def trace_fields():
        required={'run_id','step','op_id','input_hash','output_hash','state_ref','effect_request','effect_decision','recovery_ref','error_code','clock_mode'}
        return all(required<=set(e) for e in full['trace'])
    attempt('trace_required_fields','trace',trace_fields)
    from icl.api import dumps_ocir,loads_ocir,validate_ocir,run_ocir
    ir=compile_source(src)
    attempt('ocir_serializer_roundtrip','serialization',lambda: dumps_ocir(loads_ocir(dumps_ocir(ir)))==dumps_ocir(ir))
    corrupt=copy.deepcopy(ir);corrupt['source_sha256']='0'*64
    attempt('ocir_checksum_corruption','adversarial',lambda:validate_ocir(corrupt),error='CHECKSUM')
    future=copy.deepcopy(ir);future['schema_version']='99.0'
    attempt('ocir_incompatible_schema','adversarial',lambda:validate_ocir(future),error='SCHEMA_INCOMPATIBLE')
    unknown=copy.deepcopy(ir);unknown['typed_blocks'][0]['body'][0]['expr']['kind']='shell'
    unknown['integrity_sha256']=digest({k:v for k,v in unknown.items() if k!='integrity_sha256'})
    attempt('ocir_unknown_ast_opcode','adversarial',lambda:validate_ocir(unknown),error='UNSUPPORTED_OP')
    attempt('ocir_duplicate_json_key','adversarial',lambda:loads_ocir('{"schema_version":"0.1.0","schema_version":"0.1.0"}'),error='OCIR_CORRUPT')
    attempt('ocir_nonfinite_json_payload','adversarial',lambda:loads_ocir('{"x":NaN}'),error='NONFINITE')
    attempt('ocir_invalid_json','adversarial',lambda:loads_ocir('{"unfinished":'),error='OCIR_CORRUPT')
    low=compile_source('module low; fn main() -> Int64 { var i:Int64=0; while i<50 limit 60 { i=i+1; } return i; }',limits={'max_steps':20})
    attempt('runtime_cannot_raise_compiled_budget','adversarial',lambda:run_ocir(low,limits={'max_steps':21},stop_after=1)['checkpoint']['limits']['max_steps']==20)
    attempt('entry_type_rejects_bool_as_integer','adversarial',lambda:run_source('module arg; fn main(x: Int64) -> Int64 { return x; }',args=[True]),error='TYPE')
    attempt('entry_nominal_inner_type_validated','adversarial',lambda:run_source('module arg; fn main(x: Representation[Int64]) -> Int64 { return repr_value(x); }',args=[{'tag':'Representation','value':True,'observer':'o','frame':'f','unit':'m'}]),error='TYPE')
    def witness_cost_nonzero():
        out=run_source('module witness; fn main() -> RecoveryWitness { return make_witness(257,256); }')['value']
        return out['payload_bytes']>0 and out['quotient']==1 and out['remainder']==1 and out['modulus']==256
    attempt('recovery_side_information_bytes_accounted','recovery',witness_cost_nonzero)
    def diagnostics_line():
        try:compile_source('module lines;\nfn main() -> Int64 {\nreturn true;\n}')
        except Exception as e:return e.code=='TYPE' and e.span['line']==3
        return False
    attempt('source_line_diagnostic','diagnostics',diagnostics_line)
    record_source='module record_order; fn main() -> List[Int64] { let r = {z: random_int(100), a: random_int(100)}; return [r.z,r.a]; }'
    def record_roundtrip_parity():
        record_ir=compile_source(record_source)
        restored=loads_ocir(dumps_ocir(record_ir))
        values=[run_source(record_source,engine=e)['value'] for e in ('tree','vm')]+[run_ocir(restored,engine=e)['value'] for e in ('tree','vm')]
        return values==[[75,90]]*4
    attempt('record_effect_order_canonical_ocir_roundtrip','serialization',record_roundtrip_parity)
    def record_replay_canonical():
        record_ir=compile_source(record_source)
        restored=loads_ocir(dumps_ocir(record_ir))
        paused=run_source(record_source,stop_after=4)
        resumed=run_ocir(restored,checkpoint=paused['checkpoint'])
        expected=run_source(record_source)
        return resumed==expected and expected['value']==[75,90]
    attempt('record_effect_checkpoint_canonical_ocir_replay','replay',record_replay_canonical)
    return records
