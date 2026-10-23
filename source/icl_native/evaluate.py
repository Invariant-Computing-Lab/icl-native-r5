"""Frozen evaluation. Never writes model parameters or changes the dataset."""
from __future__ import annotations
import gzip,json,time,collections
import numpy as np
import torch
from .common import *
from .checkpoint import load_checkpoint
from .product import predict_many,vm_verify

def read_split(split):
    with gzip.open(ROOT/'data'/f'{split}.jsonl.gz','rt') as f:return [json.loads(s) for s in f]

def metric_records(plans,preds):
    out=[]
    for p,pred in zip(plans,preds):
        expected=[ACTIONS[i] for i in p['labels'][:p['effective_prefix']]]
        actual=pred['actions']
        # A posthoc guard cannot turn a neural mistake into a raw success.
        raw=actual==expected and pred['guard_rejection'] is None
        out.append({'example_id':p['example_id'],'semantic_group_id':p['semantic_group_id'],'world_id':p['world_id'],'reference':p['reference_result'],'expected_prefix':expected,'predicted_actions':actual,'raw_semantic_prefix_match':raw,'composed_result_match':pred['composed_result']==p['reference_result'],'positive':p['reference_result']['tag']=='Ok','confidence':pred['confidence'],'guard_rejection':pred['guard_rejection'],'journal_attempts':pred['journal_attempts'],'journal_allow_decisions':pred['journal_allow_decisions'],'first_intent':p['steps'][0]['intent']})
    return out

def stats(rows):
    def score(rs):return sum(r['raw_semantic_prefix_match'] for r in rs)/len(rs) if rs else None
    reasons=collections.Counter((r['guard_rejection'] or {}).get('reason','none') for r in rows)
    return {'n':len(rows),'raw_semantic_prefix_match':score(rows),'composed_output_match':sum(r['composed_result_match'] for r in rows)/len(rows),'positive_n':sum(r['positive'] for r in rows),'positive_raw_match':score([r for r in rows if r['positive']]),'negative_raw_match':score([r for r in rows if not r['positive']]),'guard_reasons':dict(reasons),'per_first_intent':{i:score([r for r in rows if r['first_intent']==i]) for i in INTENTS},'uncalibrated_selective_risk':{str(t):{'coverage':sum(r['confidence']>=t for r in rows)/len(rows),'raw_accuracy':score([r for r in rows if r['confidence']>=t])} for t in (0,.5,.8,.95,.99)},'original_general_M06_M07_closed':False}

def main():
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True);allstats={};kept={};start=time.time()
    runs=strict_load(ROOT/'reports/ALL_TRAINING_RUNS.json')
    for split in ('id','long','counterfactual'):
        plans=read_split(split)
        for run in runs:
            kind=run['kind'];seed=run['seed'];key=f'{kind}_{seed}'
            model,meta=load_checkpoint(ROOT/'models'/key/'best');pred=predict_many(model,plans,kind,journal_permission=True)
            rows=metric_records(plans,pred);summ=stats(rows)
            # Execute selected fresh, whole predicted ICL programs for parity; no count inflation.
            # Datagen already executed all reference programs, separately from these candidate runs.
            parity=[]
            if kind in ('native','flat'):
                for i in range(min(128,len(plans))):
                    try:
                        q=vm_verify(plans[i],pred[i],True)
                        parity.append({'example_id':plans[i]['example_id'],'executed':q['executed'],'same':q.get('runtime_consistency',True),'guard_rejected':not q['executed'],'actual_vm_effects':q.get('result',{}).get('effects',[])})
                    except Exception as e:parity.append({'example_id':plans[i]['example_id'],'executed':False,'same':False,'error':str(e)})
                if not all(q['same'] for q in parity):raise AssertionError(('WHOLE_PROGRAM_PARITY',split,key))
            summ['candidate_icl_vm_parity_checks']=len(parity);summ['actual_candidate_programs_executed']=sum(q['executed'] for q in parity);summ['candidate_icl_vm_parity_pass']=all(q['same'] for q in parity)
            d=ROOT/'reports/evaluation'/key;d.mkdir(parents=True,exist_ok=True)
            with gzip.open(d/(split+'_predictions.jsonl.gz'),'wt') as f:
                for r in rows:f.write(canonical(r)+'\n')
            dump(d/(split+'_vm_parity.json'),parity);dump(d/(split+'_summary.json'),summ)
            allstats.setdefault(key,{})[split]=summ
            if split=='long' and kind in ('native','flat'):kept[key]=rows
            print(split,key,round(summ['raw_semantic_prefix_match'],5),round(summ['positive_raw_match'] or 0,5),flush=True)
    # Cluster by semantic group; pair model seeds and groups instead of treating seed-repeated tasks as independent.
    diffs=[]
    for seed in (17,29,43):
        a,b=kept[f'native_{seed}'],kept[f'flat_{seed}'];assert [r['example_id'] for r in a]==[r['example_id'] for r in b]
        diffs.append([int(x['raw_semantic_prefix_match'])-int(y['raw_semantic_prefix_match']) for x,y in zip(a,b)])
    diff=np.asarray(diffs,dtype=float).mean(axis=0);rng=np.random.default_rng(740013)
    boot=np.asarray([rng.choice(diff,len(diff),replace=True).mean() for _ in range(1999)])
    native_times=[r['elapsed_seconds'] for r in runs if r['kind']=='native'];flat_times=[r['elapsed_seconds'] for r in runs if r['kind']=='flat']
    ratio=sum(native_times)/sum(flat_times);budget_matched=.9<=ratio<=1.1
    ci=np.quantile(boot,[.025,.975]).tolist()
    comparison={'primary':'long split raw semantic opcode prefix match','n_groups':len(diff),'seeds':[17,29,43],'paired_mean_difference':float(diff.mean()),'group_bootstrap_95_ci':ci,'bootstrap_seed':740013,'draws':1999,'conditional_on_these_three_training_seeds':True,'native_over_flat_training_wall_time_ratio':ratio,'compute_within_10_percent':budget_matched,'parameter_counts':{r['kind']:r['parameter_count'] for r in runs if r['kind'] in ('native','flat')},'claim':'SUPERIOR_IN_BOUNDED_TASK' if ci[0]>0 and budget_matched else 'BENCHMARK_INCONCLUSIVE_OR_BUDGET_UNMATCHED','not_a_general_language_model_benchmark':True}
    dump(ROOT/'reports/EVAL_SUMMARY.json',allstats);dump(ROOT/'reports/PRIMARY_COMPARISON.json',comparison);print(canonical(comparison));print('elapsed',time.time()-start)
if __name__=='__main__':main()
