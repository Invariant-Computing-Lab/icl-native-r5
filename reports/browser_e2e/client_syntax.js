const token="OFFLINE_PREVIEW_NO_AUTH_TOKEN";let runId=null;let example={
  "initial": 5,
  "memory": null,
  "steps": [
    {
      "intent": "increase",
      "arg": 3,
      "modulus": 7,
      "flags": {
        "observer_match": true,
        "frame_match": true,
        "unit_match": true,
        "witness_present": true,
        "witness_valid": true,
        "memory_present": true,
        "journal_allowed": true,
        "condition": true
      }
    },
    {
      "intent": "repeat",
      "arg": -1,
      "modulus": 7,
      "flags": {
        "observer_match": true,
        "frame_match": true,
        "unit_match": true,
        "witness_present": true,
        "witness_valid": true,
        "memory_present": true,
        "journal_allowed": true,
        "condition": true
      }
    },
    {
      "intent": "translate",
      "arg": 2,
      "modulus": 7,
      "flags": {
        "observer_match": true,
        "frame_match": true,
        "unit_match": true,
        "witness_present": true,
        "witness_valid": true,
        "memory_present": true,
        "journal_allowed": true,
        "condition": true
      }
    },
    {
      "intent": "remember",
      "arg": 0,
      "modulus": 7,
      "flags": {
        "observer_match": true,
        "frame_match": true,
        "unit_match": true,
        "witness_present": true,
        "witness_valid": true,
        "memory_present": true,
        "journal_allowed": true,
        "condition": true
      }
    },
    {
      "intent": "scale",
      "arg": 3,
      "modulus": 7,
      "flags": {
        "observer_match": true,
        "frame_match": true,
        "unit_match": true,
        "witness_present": true,
        "witness_valid": true,
        "memory_present": true,
        "journal_allowed": true,
        "condition": true
      }
    },
    {
      "intent": "recall",
      "arg": 0,
      "modulus": 7,
      "flags": {
        "observer_match": true,
        "frame_match": true,
        "unit_match": true,
        "witness_present": true,
        "witness_valid": true,
        "memory_present": true,
        "journal_allowed": true,
        "condition": true
      }
    },
    {
      "intent": "restore",
      "arg": 0,
      "modulus": 7,
      "flags": {
        "observer_match": true,
        "frame_match": true,
        "unit_match": true,
        "witness_present": true,
        "witness_valid": true,
        "memory_present": true,
        "journal_allowed": true,
        "condition": true
      }
    },
    {
      "intent": "record_add",
      "arg": -2,
      "modulus": 7,
      "flags": {
        "observer_match": true,
        "frame_match": true,
        "unit_match": true,
        "witness_present": true,
        "witness_valid": true,
        "memory_present": true,
        "journal_allowed": true,
        "condition": true
      }
    },
    {
      "intent": "axis_reverse",
      "arg": 0,
      "modulus": 7,
      "flags": {
        "observer_match": true,
        "frame_match": true,
        "unit_match": true,
        "witness_present": true,
        "witness_valid": true,
        "memory_present": true,
        "journal_allowed": true,
        "condition": true
      }
    },
    {
      "intent": "list_add",
      "arg": 1,
      "modulus": 7,
      "flags": {
        "observer_match": true,
        "frame_match": true,
        "unit_match": true,
        "witness_present": true,
        "witness_valid": true,
        "memory_present": true,
        "journal_allowed": true,
        "condition": true
      }
    }
  ]
};document.getElementById('input').value=JSON.stringify(example,null,2);document.getElementById('summary').textContent='Gerçek ağırlıklar yüklü: native seed 17; 2.774 parametre. Journal: '+"kapal\u0131";
document.getElementById('demo').onclick=()=>document.getElementById('input').value=JSON.stringify(example,null,2);
async function call(path,body){let r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-ICL-Token':token},body:JSON.stringify(body)});let v=await r.json();if(!r.ok)throw Error(JSON.stringify(v));return v;}
document.getElementById('run').onclick=async()=>{try{let v=await call('/api/run',{plan:JSON.parse(document.getElementById('input').value),permit_local_journal:document.getElementById('permit').checked});runId=v.run_id;document.getElementById('summary').textContent=JSON.stringify({run_id:runId,actions:v.proposal.actions,result:v.proposal.composed_result,guard:v.proposal.guard_rejection,vm_parity:v.verification.runtime_consistency},null,2);document.getElementById('program').textContent=v.verification.source_program||'Bağımsız kapı işlemi reddetti.';document.getElementById('full').textContent=JSON.stringify(v,null,2);}catch(e){document.getElementById('summary').textContent=e.message;}};
document.getElementById('replay').onclick=async()=>{try{if(!runId)throw Error('Önce bir görev çalıştır.');let v=await call('/api/replay',{run_id:runId});document.getElementById('summary').textContent=JSON.stringify(v,null,2);}catch(e){document.getElementById('summary').textContent=e.message;}};