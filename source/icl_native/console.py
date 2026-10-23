"""Local Invariant Cognition console: actual offline inference and durable replay.
Not the recovered legacy G51 console, not a public/multi-tenant deployment.
"""
from __future__ import annotations
import argparse,hashlib,json,secrets,sys,time,uuid
from pathlib import Path
from http.server import HTTPServer,BaseHTTPRequestHandler
from .common import canonical,strict_load,dump,sha
from .offline_infer import OfflineModel
from .execution import vm_verify,validate_plan
from icl.api import run_ocir
PAGE='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Invariant Cognition Language — R5</title>
<style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 20px;background:#f4f7fb;color:#14263b}h1{font-size:32px}small{display:block;line-height:1.5}textarea{width:100%;height:260px;box-sizing:border-box;padding:14px;font:14px monospace;border:1px solid #abbaca;border-radius:8px}button{padding:12px 18px;margin:12px 8px 12px 0;border:0;border-radius:6px;background:#163753;color:white;cursor:pointer}pre{white-space:pre-wrap;word-break:break-word;background:white;padding:18px;border-radius:8px}section{margin-top:20px}</style>
<h1>Invariant Cognition Language</h1><p>R5 · OCIL-Core 0.2.1 · Yerel araştırma prototipi</p><small>Öğrenilen bölüm: sınırlı işlem/hata seçimi. Program sözdizimi, birleştirme, kesin hesap ve yetki denetimi deterministiktir. Genel sohbet modeli değildir. Veri veya ağırlık indirmez; dış araç kullanmaz.</small>
<section><button id="demo">Örneği aç</button><button id="run">Modeli çalıştır ve doğrula</button><button id="replay">Son kaydı yeniden oynat</button><label><input type="checkbox" id="permit"> Yerel journal talebi</label><textarea id="input" spellcheck="false"></textarea></section>
<h2>Sonuç</h2><pre id="summary">Model yükleniyor…</pre><h2>Üretilen ICL programı</h2><pre id="program"></pre><details><summary>İşlem kaydı, kapsam ve doğrulama</summary><pre id="full"></pre></details>
<script>const token=__TOKEN__;let runId=null;let example=__EXAMPLE__;document.getElementById('input').value=JSON.stringify(example,null,2);document.getElementById('summary').textContent='Gerçek ağırlıklar yüklü: native seed 17; 2.774 parametre. Journal: '+__HOST__;
document.getElementById('demo').onclick=()=>document.getElementById('input').value=JSON.stringify(example,null,2);
async function call(path,body){let r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-ICL-Token':token},body:JSON.stringify(body)});let v=await r.json();if(!r.ok)throw Error(JSON.stringify(v));return v;}
document.getElementById('run').onclick=async()=>{try{let v=await call('/api/run',{plan:JSON.parse(document.getElementById('input').value),permit_local_journal:document.getElementById('permit').checked});runId=v.run_id;document.getElementById('summary').textContent=JSON.stringify({run_id:runId,actions:v.proposal.actions,result:v.proposal.composed_result,guard:v.proposal.guard_rejection,vm_parity:v.verification.runtime_consistency},null,2);document.getElementById('program').textContent=v.verification.source_program||'Bağımsız kapı işlemi reddetti.';document.getElementById('full').textContent=JSON.stringify(v,null,2);}catch(e){document.getElementById('summary').textContent=e.message;}};
document.getElementById('replay').onclick=async()=>{try{if(!runId)throw Error('Önce bir görev çalıştır.');let v=await call('/api/replay',{run_id:runId});document.getElementById('summary').textContent=JSON.stringify(v,null,2);}catch(e){document.getElementById('summary').textContent=e.message;}};</script>'''
def parse_json(b):
 def pairs(xs):
  d={}
  for k,v in xs:
   if k in d:raise ValueError('DUPLICATE_JSON_KEY')
   d[k]=v
  return d
 return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('NONFINITE')))

def serve(model_path,records,port=8065,enable_journal=False):
 model=OfflineModel(model_path);records.mkdir(parents=True,exist_ok=True);token=secrets.token_urlsafe(32)
 from .common import FLAGS
 example={'initial':5,'memory':None,'steps':[{'intent':i,'arg':a,'modulus':7,'flags':{k:True for k in FLAGS}} for i,a in [('increase',3),('remember',0),('scale',2),('recall',0)]]}
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def answer(self,status,payload,html=False):
   b=payload.encode() if html else canonical(payload).encode();self.send_response(status);self.send_header('Content-Type','text/html; charset=utf-8' if html else 'application/json');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.end_headers();self.wfile.write(b)
  def do_GET(self):
   if self.path!='/':return self.answer(404,{'error':'NOT_FOUND'})
   page=PAGE.replace('__TOKEN__',json.dumps(token)).replace('__EXAMPLE__',canonical(example)).replace('__HOST__',json.dumps('host tarafından açık' if enable_journal else 'host tarafından kapalı'))
   self.answer(200,page,True)
  def do_POST(self):
   if self.headers.get('X-ICL-Token')!=token:return self.answer(403,{'error':'LOCAL_SESSION_TOKEN_REQUIRED'})
   expected={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
   if self.headers.get('Host') not in expected:return self.answer(403,{'error':'HOST_NOT_LOCAL'})
   origin=self.headers.get('Origin')
   if origin and origin not in {'http://'+h for h in expected}:return self.answer(403,{'error':'ORIGIN_NOT_LOCAL'})
   try:
    self.connection.settimeout(10)
    if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.answer(415,{'error':'CONTENT_TYPE'})
    size=int(self.headers.get('Content-Length','0'))
    if size<2 or size>100000:return self.answer(413,{'error':'BODY_SIZE'})
    p=parse_json(self.rfile.read(size))
    if self.path=='/api/run':
     if type(p)!=dict or set(p)!={'plan','permit_local_journal'} or type(p['permit_local_journal'])!=bool:raise ValueError('REQUEST_SCHEMA')
     validate_plan(p['plan']);permit=enable_journal is True and p['permit_local_journal'] is True
     q=model.predict(p['plan'],permit);v=vm_verify(p['plan'],q,permit);runid=uuid.uuid4().hex;checkpoint=None
     if v['executed']:
      paused=run_ocir(v['ocir'],args=[p['plan']['initial'],p['plan']['memory'] or 0],stop_after=1,policy={'journal':{'allow':permit}});checkpoint=paused.get('checkpoint')
     a={'schema':'ICL_R5_LOCAL_RUN/1','run_id':runid,'model_bundle_sha256':sha(model_path/'manifest.json'),'request':p,'host_permission_effective':permit,'proposal':q,'verification':v,'checkpoint':checkpoint,'scope':'local finite prototype; no external adapters; journal is in-memory simulation'}
     # Only our derived random ID names a file, never a caller path.
     dump(records/(runid+'.json'),a);return self.answer(200,a)
    if self.path=='/api/replay':
     if type(p)!=dict or set(p)!={'run_id'} or type(p['run_id'])!=str or len(p['run_id'])!=32 or any(c not in '0123456789abcdef' for c in p['run_id']):raise ValueError('RUN_ID')
     a=strict_load(records/(p['run_id']+'.json'));permit=enable_journal is True and a['request']['permit_local_journal'] is True
     if a['checkpoint'] is None:return self.answer(409,{'error':'NO_CHECKPOINT_REJECTED_RUN'})
     v=run_ocir(a['verification']['ocir'],args=[a['request']['plan']['initial'],a['request']['plan']['memory'] or 0],checkpoint=a['checkpoint'],policy={'journal':{'allow':permit}});full=a['verification']['result']
     return self.answer(200,{'run_id':p['run_id'],'replay_value':v['value'],'value_equal':v['value']==full['value'],'trace_equal':v['trace']==full['trace'],'effect_events':v['effects'],'authority':'current independent server configuration, never checkpoint grant'})
    return self.answer(404,{'error':'NOT_FOUND'})
   except Exception as e:return self.answer(422,{'error':str(e),'type':type(e).__name__})
 server=HTTPServer(('127.0.0.1',port),Handler);print('ICL_CONSOLE_PORT='+str(server.server_port),flush=True);server.serve_forever()
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--records',type=Path,required=True);p.add_argument('--port',type=int,default=8065);p.add_argument('--enable-local-journal',action='store_true');a=p.parse_args();serve(a.model,a.records,a.port,a.enable_local_journal)
if __name__=='__main__':main()
