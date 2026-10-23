# Console integration correction
The initial HTTP checkpoint replay omitted explicit entry arguments when calling run_ocir. The language rejected the call with TYPE: entry argument count. The console now resupplies the saved validated plan arguments while resolving policy independently from current host configuration. Core, data and weights were unchanged. The failed HTTP logs are retained.
