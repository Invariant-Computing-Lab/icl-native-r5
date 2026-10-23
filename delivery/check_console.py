from pathlib import Path
import subprocess,tempfile,json,time,sys,urllib.request,urllib.error,re
R=Path(__file__).resolve().parents[1];out=R/'reports/console_e2e';out.mkdir(parents=True,exist_ok=True);records=Path(tempfile.mkdtemp(prefix='icl-console-records-'));checks=[]
def start():
 p=subprocess.Popen([sys.executable,'-I',str(R/'run_console.py'),'--port','0','--records',str(records)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 line=p.stdout.readline().strip();assert line.startswith('ICL_CONSOLE_PORT='),line
 url='http://127.0.0.1:'+line.split('=')[1];page=urllib.request.urlopen(url).read().decode();token=json.loads(re.search(r'const token=(".*?");',page).group(1));return p,url,token

def post(url,token,path,body,headers=None,raw=False):
 b=body.encode() if raw else json.dumps(body).encode();req=urllib.request.Request(url+path,data=b,headers={'Content-Type':'application/json','X-ICL-Token':token}|(headers or {}))
 try:r=urllib.request.urlopen(req,timeout=30);return r.status,json.loads(r.read())
 except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
p,url,token=start()
try:
 demo=json.loads((R/'examples/demo.json').read_text());journal=json.loads((R/'examples/denied_journal.json').read_text())
 for name,tok,body,headers,raw,expected in [
  ('token_required','bad',{'plan':demo,'permit_local_journal':False},{},False,403),
  ('cross_origin_rejected',token,{'plan':demo,'permit_local_journal':False},{'Origin':'https://invalid.example'},False,403),
  ('duplicate_json_rejected',token,'{"plan":{},"plan":{},"permit_local_journal":false}',{},True,422),
  ('large_body_rejected',token,'x'*100001,{},True,413),
  ('journal_string_not_approval',token,{'plan':demo,'permit_local_journal':'true'},{},False,422),
  ('real_model_demo',token,{'plan':demo,'permit_local_journal':False},{},False,200),
  ('caller_cannot_override_host_journal',token,{'plan':journal,'permit_local_journal':True},{},False,200)]:
  status,res=post(url,tok,'/api/run',body,headers,raw);assert status==expected,(name,status,res)
  if name=='real_model_demo':assert res['verification']['result']['value']=={'tag':'Ok','value':-4};run_id=res['run_id']
  if name=='caller_cannot_override_host_journal':assert not res['host_permission_effective'] and res['verification']['result']['effects']==[] and res['verification']['result']['value']=={'tag':'Err','error':'EFFECT_DENIED'}
  (out/(name+'.json')).write_text(json.dumps(res,indent=2));checks.append({'case':name,'status':'PASS','http_status':status})
 status,res=post(url,token,'/api/replay',{'run_id':'../escape'});assert status==422;checks.append({'case':'replay_path_traversal_rejected','status':'PASS'})
 status,res=post(url,token,'/api/replay',{'run_id':run_id});(out/'replay_actual_first.json').write_text(json.dumps({'status':status,'response':res},indent=2));assert status==200 and res['value_equal'] and res['trace_equal'];checks.append({'case':'persistent_checkpoint_replay','status':'PASS'})
finally:p.terminate();p.wait(timeout=10)
p,url,token=start()
try:
 status,res=post(url,token,'/api/replay',{'run_id':run_id});(out/'replay_actual_first.json').write_text(json.dumps({'status':status,'response':res},indent=2));assert status==200 and res['value_equal'] and res['trace_equal'];checks.append({'case':'restart_then_replay_existing_record','status':'PASS'});(out/'restart_replay.json').write_text(json.dumps(res,indent=2))
finally:p.terminate();p.wait(timeout=10)
(out/'SUMMARY.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'model_backend':'actual offline trained model; ICL VM','browser_visual_test':'NOT_RUN; HTTP and request/control flow tested','network_scope':'localhost binding; not public deployment or OS sandbox certification'},indent=2));print('CONSOLE_PASS',len(checks))
