from pathlib import Path
import json,sys,platform,importlib.metadata as md
R=Path(__file__).resolve().parents[1];c=R/'source/icl_core'
p=c/'LANGUAGE_SPEC.md';s=p.read_text().replace('ICL-Core 0.1 language specification','ICL-Core 0.2.1 language specification')
s=s.replace('declarations and one or more named function declarations.','declarations, optional local type aliases, and one or more named function declarations.')
s=s.replace('`var`, `if`, `else`, `while`, `limit`, `return`, `true`, and `false`.','`var`, `if`, `else`, `while`, `limit`, `return`, `true`, `false`, and `type`.')
s=s.replace('Empty lists parse but fail type checking because contextual empty-list typing is\nnot implemented.', 'Empty lists require a List[T] context from a declared binding, argument,\nreturn or assignment. Unconstrained `let x=[];` is rejected.')
s=s.replace('| inferred record | Named fields and structural field access |','| `Record{field:T,...}` | Structural fields in local, parameter and return annotations |')
a=s.index('The bracket notation above');b=s.index('Both operands of arithmetic',a)
s=s[:a]+'''Local aliases use `type State = Record{count:Int64,value:Float64};` and must\nprecede use. They expand into structural types; no recursive, generic or forward\naliases are supported. Aliases do not create nominal identity. Record field types\nare normalized in lexicographic order, including across explicit module maps.\nUser-defined generic functions/type parameters and algebraic data declarations\nremain unsupported. Lists and tuples serialize as arrays but retain static types.\n\n'''+s[b:];s=s.replace('version `0.1.0`','version `0.2.1`');p.write_text(s)
p=c/'grammar.ebnf';s=p.read_text();s=s.replace('ICL-Core 0.1','ICL-Core 0.2.1');s=s.replace('{ import_decl }, function_decl, { function_decl }','{ import_decl }, { alias_decl }, function_decl, { function_decl }')
# Inspectable explicit productions, while parser code remains normative for declaration ordering.
s=s.replace('type_syntax    = identifier, [ "[", [ type_argument, { ",", type_argument } ], "]" ] ;','''alias_decl     = "type", identifier, "=", type_syntax, ";" ;\ntype_syntax    = "Record", "{", [ type_field, { ",", type_field } ], "}"\n               | identifier, [ "[", [ type_argument, { ",", type_argument } ], "]" ] ;\ntype_field     = identifier, ":", type_syntax ;''')
s=s.replace('- Empty lists parse but are rejected by the finite type checker.','- Empty lists require an explicit List[T] context at type checking.')
s=s.replace('- Record annotations, function types, type aliases, and first-class functions\n     are unsupported. Record literal field names must be unique.','- Record annotations and prior local aliases are supported; aliases cannot\n     be generic, recursive or forward declarations. Function types and first-class\n     functions are unsupported. Record literal/type field names must be unique.')
p.write_text(s)
p=c/'README.md';s=p.read_text().replace('0.1.0','0.2.1');s=s.replace('This release is a **NEW_IMPLEMENTATION**','This release is a **NEW_VERSION_ON_RECOVERED_CORE**');s+='''\n## R5 changes and limits\nRecord annotations, local aliases and contextual empty lists extend the preserved\n0.1.0 core. See `LANGUAGE_SPEC.md` and the 31 extension cases in the enclosing\nrelease. The R5 neural opcode model is a separate bounded component. New grammar\nand token metadata do not imply new general type-soundness or clinical results.\nOriginal archive, source bundle and historical results are in `originals/` at the\nrelease root; no original frozen file was overwritten.\n''';p.write_text(s)
(c/'CHANGELOG.md').write_text('''# 0.2.1 / R5\nNew structural record annotations and local type aliases; contextual empty list\ntyping. Versioned OCIR metadata and token vocabulary. The old 0.1.0 archive is\nunchanged. One parser bug in return-alias handling was caught and corrected by\nthe new tests; initial failure log retained. No general soundness claim.\n''')
lock={'python':platform.python_version(),'implementation':platform.python_implementation(),'training_dependencies':{k:md.version(k) for k in ['torch','numpy','safetensors']},'test_dependencies':{'pytest':md.version('pytest')},'build_dependencies':{'setuptools':md.version('setuptools'),'wheel':'bundled bdist_wheel via setuptools; no separate distribution metadata'},'language_and_offline_model_runtime_dependencies':[],'scope':'Exact observed versions; runtime works in clean venv without network downloads. Not proof of all Python/platform compatibility.'}
(c/'environment.lock').write_text(json.dumps(lock,indent=2)+'\n')
# Stale historical manifests must never masquerade as the changed source release's manifest.
for n in ['MANIFEST.json','RESUME.json','LANGUAGE_HANDOFF.json']:
 if (c/n).exists(): (c/n).unlink()
# Remove historical wheel from active new source delivery, preserve it in originals.
for p in (c/'dist').glob('*'):p.unlink()
print('updated documentation metadata')
