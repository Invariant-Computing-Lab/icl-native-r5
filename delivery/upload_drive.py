"""Explicit user OAuth upload for Google Colab. No passwords/tokens are printed.
This is a user-run transfer utility, NOT evidence of an upload by ChatGPT.
Only new private version folders are created. Existing different bytes are never overwritten.
"""
from pathlib import Path
import hashlib,json,os,tempfile,zipfile,time,shutil
from verify_archive import validate,PREFIX
PARENTS={'control':'1cE4POvzQkrhGZeEXEtdyfOaQXKybvL70','core':'1l051Boq6aF9L8QzY0lCy0mJrVd4r1hBv','model':'1UjNgl7NEFYAMUMEYOX9a_0_9fGWndNMk','registry':'1sIbxe8NCS4nDfOeHbhnCQjDa_JDFPCT5'}
VERSION='2026-10-13_R5_VERIFIED_LOCAL_DELIVERY'
EXPECTED_ACCOUNT='houyinkyoma357@gmail.com'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def qquote(s):return s.replace('\\','\\\\').replace("'","\\'")
def main(archive):
 archive=Path(archive);local=validate(archive);print('Yerel gerçek içerik doğrulandı:',local)
 from google.colab import auth
 auth.authenticate_user()
 import google.auth
 from googleapiclient.discovery import build
 from googleapiclient.http import MediaFileUpload,MediaIoBaseDownload
 credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/drive']);service=build('drive','v3',credentials=credentials,cache_discovery=False)
 user=service.about().get(fields='user(emailAddress)').execute()['user']['emailAddress']
 if user.lower()!=EXPECTED_ACCOUNT.lower():raise RuntimeError('Yanlış hesap. Primary Google hesabıyla yetkilendir; hiçbir dosya yüklenmedi.')
 def metadata(fid):return service.files().get(fileId=fid,fields='id,name,mimeType,size,parents,shared',supportsAllDrives=True).execute()
 for parent in PARENTS.values():
  m=metadata(parent)
  if m.get('mimeType')!='application/vnd.google-apps.folder' or m.get('shared'):raise RuntimeError('Özel hedef klasör doğrulanamadı; paylaşım ayarı değiştirilmeden duruldu.')
 def find(parent,name):
  q=f"'{qquote(parent)}' in parents and trashed=false and name='{qquote(name)}'";found=[];token=None
  while True:
   r=service.files().list(q=q,fields='files(id,name,mimeType,size),nextPageToken',pageSize=100,pageToken=token,supportsAllDrives=True,includeItemsFromAllDrives=True).execute();found.extend(r.get('files',[]));token=r.get('nextPageToken')
   if not token:break
  if len(found)>1:raise RuntimeError('Aynı adlı birden fazla hedef var; tahmin edilmedi: '+name)
  return found[0] if found else None
 def folder(parent,name):
  old=find(parent,name)
  if old:
   if old['mimeType']!='application/vnd.google-apps.folder':raise RuntimeError('Klasör/dosya adı çakışması')
   return old['id']
  return service.files().create(body={'name':name,'mimeType':'application/vnd.google-apps.folder','parents':[parent]},fields='id',supportsAllDrives=True).execute()['id']
 targets={k:folder(v,VERSION) for k,v in PARENTS.items()};receipts=[]
 def remote_hash(fid):
  with tempfile.TemporaryFile() as f:
   dl=MediaIoBaseDownload(f,service.files().get_media(fileId=fid,supportsAllDrives=True),chunksize=8*1024*1024);done=False
   while not done:_,done=dl.next_chunk(num_retries=3)
   f.seek(0);h=hashlib.sha256()
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
   return h.hexdigest()
 def put(path,parent):
  path=Path(path);digest=sha(path);old=find(parent,path.name)
  if old:
   if int(old.get('size','-1'))!=path.stat().st_size or remote_hash(old['id'])!=digest:raise RuntimeError('Mevcut farklı dosyanın üzerine yazılmadı: '+path.name)
   fid=old['id'];mode='ALREADY_PRESENT_READBACK_VERIFIED'
  else:
   req=service.files().create(body={'name':path.name,'parents':[parent],'appProperties':{'icl_release':'R5','local_sha256':digest}},media_body=MediaFileUpload(str(path),resumable=True,chunksize=8*1024*1024),fields='id,size',supportsAllDrives=True);response=None
   while response is None:_,response=req.next_chunk(num_retries=3)
   fid=response['id'];mode='UPLOADED_READBACK_VERIFIED'
   if remote_hash(fid)!=digest:raise RuntimeError('Uzak SHA-256 eşleşmedi: '+path.name)
  m=metadata(fid)
  if m.get('shared') or parent not in m.get('parents',[]):raise RuntimeError('Uzak paylaşım/üst klasör denetimi başarısız')
  receipt={'name':path.name,'id':fid,'parent_id':parent,'bytes':path.stat().st_size,'sha256':digest,'readback_match':True,'mode':'CONTENT_READBACK_VERIFIED','url':'https://drive.google.com/file/d/'+fid+'/view'};receipts.append(receipt)
  print(path.name,'→ doğrulandı');return receipt
 with tempfile.TemporaryDirectory(prefix='icl-r5-transfer-') as td:
  td=Path(td)
  # Validation above covers path, membership, symlink, size and hash before extraction.
  with zipfile.ZipFile(archive) as z:z.extractall(td)
  r=td/'ICL_R5_20261013';normalized=td/'ICL_R5_DOGRULANMIS_TESLIM_20261013.zip';shutil.copy2(archive,normalized);put(normalized,targets['control'])
  def subzip(name,predicate):
   p=td/name
   with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(r.rglob('*')):
     if f.is_file() and predicate(f.relative_to(r).as_posix()):
      info=zipfile.ZipInfo(f.relative_to(r).as_posix(),date_time=(2026,10,13,0,0,0));info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,f.read_bytes())
   return p
  core=subzip('ICL_CORE_0.2.1_R5_SOURCE.zip',lambda n:n.startswith('source/icl_core/') or n in ('LANGUAGE_HANDOFF.json','README_TR.md'))
  model=subzip('ICL_NATIVE_R5_MODELS_CODE_EVIDENCE.zip',lambda n:n.startswith(('source/icl_native/','models/','reports/','examples/')) or n in ('run_local.py','run_console.py','MODEL_CARD.md','README_TR.md'))
  data=subzip('ICL_R5_DATA_AND_REFERENCE_AUDIT.zip',lambda n:n.startswith('data/'))
  put(core,targets['core']);put(r/'source/icl_core/dist/invariant_cognition_language-0.2.1-py3-none-any.whl',targets['core']);put(r/'LANGUAGE_HANDOFF.json',targets['core'])
  put(model,targets['model']);put(data,targets['model']);put(r/'MODEL_CARD.md',targets['model']);put(r/'reports/EVAL_SUMMARY.json',targets['model'])
  for name in ('SONUC_RAPORU_TR.md','CURRENT_STATUS.json','TASK_LEDGER.json','MANIFEST.json','PROJECT_MEMORY.md'):put(r/name,targets['control'])
  body={'schema':'ICL_R5_DRIVE_READBACK/1','account_verified':True,'folders':targets,'local_archive_sha256':sha(archive),'assets':receipts.copy(),'all_assets_readback_verified':True,'model_scope':'bounded semantic opcode kernel; original broad model gates not automatically complete','public_release':False,'permissions_changed':False}
  p=Path.cwd()/'ICL_R5_DRIVE_READBACK.json';p.write_text(json.dumps(body,indent=2)+'\n');final=put(p,targets['registry']);print('Aktarım bitti. Makbuz:',final['url'])
 return body
if __name__=='__main__':
 import sys
 main(sys.argv[1])
