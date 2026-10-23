"""Offline visual rendering ONLY. It does not bypass the browser network policy.
Displayed result is a previously executed, recorded CLI result, not new inference.
"""
from pathlib import Path
import sys,json,re,subprocess
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'source'),str(R/'source/icl_core')]
from icl_native.console import PAGE
from icl_native.common import canonical
from playwright.sync_api import sync_playwright
out=R/'reports/browser_e2e';out.mkdir(exist_ok=True)
p=PAGE.replace('__TOKEN__',json.dumps('OFFLINE_PREVIEW_NO_AUTH_TOKEN')).replace('__EXAMPLE__',(R/'examples/demo.json').read_text()).replace('__HOST__',json.dumps('kapalı'))
p=p.replace('<h1>','<p style="padding:12px;border:2px solid #163753">Kayıtlı CLI sonucunun çevrimdışı görünümü. Tarayıcıdaki canlı ağ akışı bu ortamın yönetici politikası nedeniyle test edilmedi.</p><h1>',1)
js=re.search(r'<script>(.*?)</script>',p,re.S).group(1);(out/'client_syntax.js').write_text(js);n=subprocess.run(['node','--check',str(out/'client_syntax.js')],text=True,capture_output=True);assert n.returncode==0,n.stderr
record=json.loads((R/'reports/DEMO_RESULT.json').read_text())
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':1320,'height':980});page.set_content(p)
 page.evaluate('r=>{document.querySelector("#summary").textContent=JSON.stringify({kayitli_sonuc:r.proposal.composed_result,ogrenilmis_islemler:r.proposal.actions,vm_uyumu:r.verification.runtime_consistency},null,2);document.querySelector("#program").textContent=r.verification.source_program;}',record)
 page.screenshot(path=str(out/'console_recorded_preview.png'),full_page=True);b.close()
(out/'SUMMARY.json').write_text(json.dumps({'live_browser_e2e':'BLOCKED_BY_ADMINISTRATOR_NETWORK_POLICY','original_error':'Page.goto net::ERR_BLOCKED_BY_ADMINISTRATOR at local server','policy_not_bypassed':True,'offline_render':'PASS','client_javascript_syntax':'PASS_NODE_CHECK','preview_source':'reports/DEMO_RESULT.json, previously executed CLI result; no new browser inference','separate_live_HTTP_tests':'reports/console_e2e/SUMMARY.json'},indent=2)+'\n');print('OFFLINE_PREVIEW_PASS; LIVE_BROWSER_E2E_BLOCKED')
