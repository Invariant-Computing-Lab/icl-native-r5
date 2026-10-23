from pathlib import Path
import sys,gzip,json,time,itertools
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'source'),str(R/'source/icl_core')]
from icl_native.common import digest,dump,sha,canonical
from icl_native.reference_program import reference_source,reference_arguments
from icl.api import compile_source,run_ocir,canonicalize_source
out=R/'data/reference_ast_audit';out.mkdir(exist_ok=True)
def erase_literals(n):
 if isinstance(n,dict):
  return {k:('__literal_'+type(v).__name__ if n.get('kind')=='literal' and k=='value' else erase_literals(v)) for k,v in n.items()}
 if isinstance(n,list):return [erase_literals(v) for v in n]
 return n
sets={};specialized={};counts={};start=time.time()
for split in ['train','validation','id','long','counterfactual']:
 keys=set();targets=set();n=0;families=set();compiled=0
 with gzip.open(R/'data'/f'{split}.jsonl.gz','rt') as f,gzip.open(out/f'{split}_reference_programs.jsonl.gz','wt') as g:
  for line in f:
   p=json.loads(line);src=reference_source(p);o=compile_source(src);actual=run_ocir(o,args=reference_arguments(p),policy={'journal':{'allow':True}})['value']
   if actual!=p['reference_result']:raise AssertionError((p['example_id'],actual,p['reference_result']))
   key=digest(erase_literals(canonicalize_source(src)));keys.add(key);targets.add(p['source_sha256']);families.add(p['semantic_group_id']);n+=1
   g.write(canonical({'example_id':p['example_id'],'input_task_ast_group':key,'semantic_group_id':p['semantic_group_id'],'source':src,'ocir_program_id':o['program_id'],'actual':actual,'arguments':reference_arguments(p)})+'\n')
 sets[split]=keys;specialized[split]=targets;counts[split]={'programs_reexecuted':n,'distinct_task_ast_groups':len(keys),'declared_intent_plan_groups':len(families),'distinct_specialized_candidate_target_texts':len(targets)}
 print(split,counts[split],time.time()-start,flush=True)
result={'audit':'ICL_R5_GENERIC_RUNTIME_CONTEXT_REFERENCE/1','status':'PASS' if all(not(sets[a]&sets[b]) for a,b in itertools.combinations(sets,2)) else 'FAIL_AST_OVERLAP','input_task_ast_intersections':{a+'|'+b:len(sets[a]&sets[b]) for a,b in itertools.combinations(sets,2)},'specialized_target_source_intersections':{a+'|'+b:len(specialized[a]&specialized[b]) for a,b in itertools.combinations(sets,2)},'counts':counts,'scope':'Input-program AST grouping, literal-erased; not all mathematical program equivalences. Identical specialized error outputs can occur across splits and are disclosed; they are not novel source-generation evidence. Training consumed local feature/action supervision, not source strings.','post_training_audit_not_new_model_selection':True,'new_generic_reference_uses_runtime_context':True,'elapsed_seconds':time.time()-start,'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in out.glob('*.gz')}}
dump(out/'SUMMARY.json',result);print(result['status'],flush=True)
