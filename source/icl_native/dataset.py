"""Fresh structured-plan corpus; all variants of a symbolic root share one split.
Reported R4 failures motivate NEW data, not a recovered R4 replication.
"""
from __future__ import annotations
import gzip,json,random,collections,time,copy,sys
from pathlib import Path
import numpy as np
from .common import *
from .emitter import emit
sys.path.insert(0,str(ROOT/'source/icl_core'))
from icl.api import compile_source,run_ocir
SPLITS={'train':20000,'validation':2000,'id':2000,'long':2000,'counterfactual':2000}
SEEDS={'structure':71931,'numeric':89123,'flags':51243}
def generate():
    d=ROOT/'data';d.mkdir(exist_ok=True)
    if (d/'DATA_MANIFEST.json').exists():raise RuntimeError('REFUSE_OVERWRITE_FROZEN_DATASET')
    struct=random.Random(SEEDS['structure']);nums=random.Random(SEEDS['numeric']);flags=random.Random(SEEDS['flags'])
    seen=set();groups={};plans={}
    for split,n in SPLITS.items():
        seqs=[]
        while len(seqs)<n:
            length=struct.randint(12,20) if split=='long' else struct.randint(4,7)
            seq=tuple(struct.choice(INTENTS) for _ in range(length));key=digest(seq)
            if key in seen:continue
            seen.add(key);seqs.append((key,seq))
        groups[split]=[k for k,_ in seqs];plans[split]=seqs
    dump(d/'GROUP_SPLIT_LOCK.json',{'seeds':SEEDS,'semantic_group_ids':groups,'definition':'ordered intent sequence with literals/context removed; all numeric/flag/orbit variants in one split','assigned_before_numeric_and_flag_generation':True})
    manifests=[];audits={};worlds=set();start=time.time()
    for split,seqs in plans.items():
        xs=[];ys=[];group_rows=[];records=[];positive=0;worldset=set();errs=collections.Counter()
        for idx,(key,seq) in enumerate(seqs):
            initial=nums.randint(-100000,100000);memory=nums.randint(-100000,100000) if flags.random()<.5 else None
            steps=[{'intent':i,'arg':nums.randint(-3,3),'modulus':nums.randint(2,11),'flags':{k:bool(flags.getrandbits(1)) for k in FLAGS}} for i in seq]
            if bool(flags.getrandbits(1)):
                mp=memory is not None
                for s in steps:
                    f=s['flags']
                    if s['intent']=='translate':f['observer_match']=f['frame_match']=f['unit_match']=True
                    if s['intent']=='restore':f['witness_present']=f['witness_valid']=True
                    if s['intent']=='journal':f['journal_allowed']=True
                    if s['intent']=='recall' and not mp:memory=nums.randint(-100000,100000);mp=True
                    if s['intent']=='remember':mp=True
            wid=digest({'initial':initial,'memory':memory,'args':[(s['arg'],s['modulus']) for s in steps]})
            if wid in worlds:raise RuntimeError('NUMERIC_WORLD_COLLISION')
            worlds.add(wid);worldset.add(wid)
            rec={'example_id':f'{split}_{idx:06d}','split':split,'semantic_group_id':key,'canonical_program_id':key,'observer_orbit_id':key,'world_id':wid,'initial':initial,'memory':memory,'steps':steps,'lineage':'R5_NEW_SYNTHETIC/ICL_0.2.1','rights':'new project synthetic code, private release','variant':'base'}
            variants=[rec]
            if split=='counterfactual':
                twin=copy.deepcopy(rec);twin['example_id']+='_flipped';twin['variant']='all_guard_bits_flipped_same_numbers'
                for s in twin['steps']:
                    for k in FLAGS:s['flags'][k]=not s['flags'][k]
                variants.append(twin)
            for r in variants:
                x,y,expected,prefix,states=target_steps(r);src=emit(r,[ACTIONS[i] for i in y]);ocir=compile_source(src)
                result=run_ocir(ocir,args=[r['initial'],r['memory'] or 0],policy={'journal':{'allow':True}})['value']
                if result!=expected:raise AssertionError((r['example_id'],result,expected))
                r.update({'labels':y,'reference_result':expected,'effective_prefix':prefix,'source_program':src,'source_sha256':hashlib.sha256(src.encode()).hexdigest(),'ocir_sha256':digest(ocir),'feature_rows':x})
                records.append(r);xs.extend(x);ys.extend(y);group_rows.extend([idx]*len(y));positive+=expected['tag']=='Ok'
                if expected['tag']=='Err':errs[expected['error']]+=1
        with gzip.open(d/(split+'.jsonl.gz'),'wt',encoding='utf8') as f:
            for r in records:f.write(canonical(r)+'\n')
        if split in ('train','validation'):np.savez_compressed(d/(split+'.npz'),X=np.asarray(xs,dtype=np.float32),y=np.asarray(ys,dtype=np.int64),groups=np.asarray(group_rows,dtype=np.int32))
        audits[split]={'semantic_groups':len(seqs),'examples':len(records),'supervised_nodes':len(ys),'icl_oracle_programs_executed':len(records),'positive_examples':positive,'negative_examples':len(records)-positive,'error_counts':dict(errs),'world_ids':sorted(worldset)}
        manifests.append({'file':split+'.jsonl.gz','bytes':(d/(split+'.jsonl.gz')).stat().st_size,'sha256':sha(d/(split+'.jsonl.gz'))})
        print(split,{k:v for k,v in audits[split].items() if k!='world_ids'},'seconds',round(time.time()-start,2),flush=True)
    dump(d/'split_audit.json',{'canonical_semantic_orbit_intersections':{a+'|'+b:len(set(groups[a])&set(groups[b])) for a in groups for b in groups if a<b},'world_id_intersections':{a+'|'+b:len(set(audits[a]['world_ids'])&set(audits[b]['world_ids'])) for a in audits for b in audits if a<b},'splits':{k:{q:w for q,w in v.items() if q!='world_ids'} for k,v in audits.items()},'canonical_definition':'entire ordered intent plan; literals/flags removed, primitives shared for compositional learning','world_generation':'independent RNG; guard bits not derived from parity, residue or magnitude','counterfactual_pairs_same_numbers_one_split':True})
    dump(d/'DATA_MANIFEST.json',{'dataset_id':'ICL_R5_FRESH_FACTORIAL_20261013','generator_sha256':sha(Path(__file__)),'split_lock_sha256':sha(d/'GROUP_SPLIT_LOCK.json'),'files':manifests,'new_not_recovered_R4':True,'semantics':'bounded structured-intent to opcode plans; syntax emitter and execution oracle external to learned model','elapsed_seconds':time.time()-start})
if __name__=='__main__':generate()
