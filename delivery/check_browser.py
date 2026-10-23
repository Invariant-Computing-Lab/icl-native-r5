from pathlib import Path
import subprocess,tempfile,json,sys
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];out=R/'reports/browser_e2e';out.mkdir(parents=True,exist_ok=True)
p=subprocess.Popen([sys.executable,'-I',str(R/'run_console.py'),'--port','0','--records',tempfile.mkdtemp(prefix='icl-browser-records-')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
line=p.stdout.readline().strip();assert line.startswith('ICL_CONSOLE_PORT=');url='http://127.0.0.1:'+line.split('=')[1];checks=[];errors=[];requests=[]
try:
 with sync_playwright() as w:
  browser=w.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage']);page=browser.new_page(viewport={'width':1320,'height':980});page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url));page.goto(url)
  assert 'native seed 17' in page.locator('#summary').inner_text();checks.append('real_model_loaded_page')
  page.locator('#input').fill((R/'examples/demo.json').read_text());page.locator('#run').click();page.wait_for_function("document.querySelector('#summary').textContent.includes('-4')")
  assert 'module native_plan' in page.locator('#program').inner_text();checks.append('browser_model_to_icl_vm_demo')
  page.screenshot(path=str(out/'console_demo.png'),full_page=True)
  page.locator('#replay').click();page.wait_for_function("document.querySelector('#summary').textContent.includes('trace_equal')");assert json.loads(page.locator('#summary').inner_text())['trace_equal'];checks.append('browser_checkpoint_replay')
  page.locator('#input').fill((R/'examples/denied_journal.json').read_text());page.locator('#permit').check();page.locator('#run').click();page.wait_for_function("document.querySelector('#summary').textContent.includes('EFFECT_DENIED')");checks.append('browser_caller_checkbox_cannot_grant_host_authority')
  q=json.loads((R/'examples/demo.json').read_text());q['steps'][0]['flags']['condition']='true';page.locator('#input').fill(json.dumps(q));page.locator('#run').click();page.wait_for_function("document.querySelector('#summary').textContent.includes('FLAGS_SCHEMA')");checks.append('browser_invalid_typed_input')
  assert not errors,errors;assert all(u.startswith(url) for u in requests),requests;checks.append('no_page_errors_or_external_requests');browser.close()
finally:p.terminate();p.wait(timeout=10)
(out/'SUMMARY.json').write_text(json.dumps({'status':'PASS','checks':checks,'passed':len(checks),'browser':'headless system Chromium via Playwright','page_errors':errors,'external_requests':[],'scope':'actual DOM/request/model/replay workflows, not public multi-tenant penetration test'},indent=2)+'\n');print('BROWSER_PASS',len(checks))
