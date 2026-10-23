from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1];S=R/'source/icl_native';core=R/'source/icl_core'
for p in (core/'TOKEN_VOCAB.json',core/'icl/TOKEN_VOCAB.json'):
 d=json.loads(p.read_text());d['version']='0.2.1';d['keywords']=sorted(set(d['keywords'])|{'type'});p.write_text(json.dumps(d,indent=2)+'\n')
p=S/'product.py';s=p.read_text();a=s.index('def validate_plan(');b=s.index('@torch.no_grad()')
functions=s[a:b];v=s[s.index('def vm_verify('):s.index('def main():')]
execution='''"""Pure deterministic control/verification. No trained model or teaching oracle here.
These functions supply exact execution, not learned state prediction."""\nfrom .common import ERRORS,validate_step\nfrom .emitter import emit\nfrom icl.runtime import checked_binary,checked_unary,ICLError\nfrom icl.api import compile_source,run_ocir\n\n'''+functions+v
(S/'execution.py').write_text(execution)
s=s[:a]+'from .execution import validate_plan,protocol_guard,advance_runtime,vm_verify\n\n'+s[b:s.index('def vm_verify(')]+s[s.index('def main():'):]
s=s.replace("'journal_executed_local':ok,'external_operations_executed':0","'journal_allow_decisions':ok,'execution_scope':'host state simulation; actual ICL effects are in verification.result.effects'")
p.write_text(s)
p=S/'evaluate.py';s=p.read_text().replace("'journal_local_executions':pred['journal_executed_local'],'unauthorized_executions':0,","'journal_allow_decisions':pred['journal_allow_decisions'],")
s=s.replace("'guard_rejected':not q['executed']}","'guard_rejected':not q['executed'],'actual_vm_effects':q.get('result',{}).get('effects',[])}")
s=s.replace("summ['candidate_icl_vm_parity_checks']=len(parity);", "summ['candidate_icl_vm_parity_checks']=len(parity);summ['actual_candidate_programs_executed']=sum(q['executed'] for q in parity);")
p.write_text(s)
p=S/'emitter.py';s=p.read_text().replace('# For valid examples witness contains the quotient; neither model nor code promises recovery without it.\n            # Actual witness content/corruption is independently checked by the product wrapper before execution.', '# Synthetic known-state roundtrip: witness is made from x, not recovered from unknown data.\n            # The wrapper checks supplied boolean scenario conditions, NOT an external witness signature.')
p.write_text(s)
# Preserve the first evaluator output before correcting the presentation of decision vs execution counts.
old=R/'reports/evaluation_first_schema';
if not old.exists():shutil.copytree(R/'reports/evaluation',old)
(R/'reports/MEASUREMENT_SCHEMA_CORRECTION.md').write_text('''# Measurement-schema correction (no retraining)\nThe first R5 evaluator called simulated journal allow decisions executions and emitted a literal zero unauthorized-execution field. Those fields were removed/corrected before release. First outputs are retained only in evaluation_first_schema as superseded audit records, not final statistics. Actual VM execution and actual effect records are now counted separately. Data, model weights, model selection and scoring targets were not changed.\n''')
