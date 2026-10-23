import sys,json,importlib.util
from pathlib import Path
source=Path(sys.argv.pop(1));request=Path(sys.argv.pop(1));output=Path(sys.argv.pop(1));permit=sys.argv.pop(1)=='yes'
assert importlib.util.find_spec('torch') is None
assert importlib.util.find_spec('numpy') is None
import icl
assert 'site-packages' in icl.__file__
def audit(event,args):
 if event.startswith('socket.'):raise PermissionError('NETWORK_BLOCKED_BY_PYTHON_AUDIT')
sys.addaudithook(audit)
import socket
try:socket.socket();raise AssertionError('socket permitted')
except PermissionError:pass
sys.path.insert(0,str(source/'source'))
from icl_native.offline_infer import main
rc=main(['--model',str(source/'models/offline_native_17'),'--request',str(request),'--output',str(output)]+(['--permit-local-journal'] if permit else []))
assert not any(k=='torch' or k.startswith('numpy') for k in sys.modules)
raise SystemExit(rc)
