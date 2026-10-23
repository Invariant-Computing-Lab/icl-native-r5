from pathlib import Path
import sys
R=Path(__file__).resolve().parent
sys.path[:0]=[str(R/'source'),str(R/'source/icl_core')]
from icl_native.console import main
args=sys.argv[1:]
if '--model' not in args:args=['--model',str(R/'models/offline_native_17')]+args
if '--records' not in args:args=['--records',str(R/'local_runs')]+args
sys.argv=[sys.argv[0]]+args
main()
