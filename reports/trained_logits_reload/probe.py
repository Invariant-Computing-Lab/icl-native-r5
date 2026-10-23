import sys,json,importlib.util
from pathlib import Path
r=Path(sys.argv[1]);assert importlib.util.find_spec('torch') is None and importlib.util.find_spec('numpy') is None
import icl
assert 'site-packages' in icl.__file__
def audit(e,a):
 if e.startswith('socket.'):raise PermissionError('NETWORK_BLOCKED')
sys.addaudithook(audit)
sys.path.insert(0,str(r/'source'))
from icl_native.offline_infer import OfflineModel
m=OfflineModel(r/'models/offline_native_17');rows=json.loads((r/'reports/trained_logits_reload/fixtures.json').read_text());out=[m.logits(row) for row in rows];print(json.dumps(out))
