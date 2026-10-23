"""Run from anywhere: python -I /path/to/run_local.py --request /path/request.json.
This entry point imports only bundled code and the Python standard library.
"""
from pathlib import Path
import sys
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'source'));sys.path.insert(0,str(R/'source/icl_core'))
from icl_native.offline_infer import main
args=sys.argv[1:]
if '--model' not in args:args=['--model',str(R/'models/offline_native_17')]+args
raise SystemExit(main(args))
