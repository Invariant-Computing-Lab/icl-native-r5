# ICL-Core / OCIR teknik sözleşmesi
10 Ekim 2026 · Tasarım hedefi, henüz uygulanmış compiler iddiası değil

## Ortak kimlik
Dil: Invariant Cognition Language. Araştırma sahibi: OCIL/OCIR. Ürünleştirme: Invariant OS. Dil-core hedefi OCIL-LANG-01, AI ürünü IOS-ICL-01. OCIL eski metinleri tek başına v0.1 grameri sağlamaz; aşağıdaki ayrıntılar yeni mühendislik sözleşmesidir.

## Program yapısı ve kapsam
Source file `.icl`; manifest `icl.toml` veya eşdeğer tek belgelenmiş biçim; import yalnız explicit module map. v0.1: lexical scope, fonksiyon, tipli parametre/return, let/mutable local, if/else, bounded loop, records/lists, checked arithmetic, Result hata taşıma, observer/context değeri, recovery/checkpoint ve typed small-tensor ops. Proje/package/entrypoint ve kaynak satırı diagnostics zorunludur.

Bir sayısal mini DSL'den farkı, birden fazla modülde yeniden kullanılabilir programların typed execution'ıdır. Genel amaçlı genişleme yolu korunur; v0.1'in sonlu fuel sınırı göz ardı edilerek evrensel termination/decidability iddiası kurulmaz. Eğitimde kullanılan sınırlı alt dil ile gelecek genel dil iddiaları ayrılır.

## Ayrı sözleşmeler
1. **Representational round-trip:** aynı serileştirme sözleşmesiyle decode(encode(v)) = v. Float bit koruma gerekiyorsa NaN/Inf politika ve encoding açıkça belirtilir; aksi durumda yalnız declared finite values kapsamı.
2. **Observer reconstruction:** y=H_o(x,c) kaynak state'i tekil belirlemeyebilir. Gözlenmeyen yönü modelin tahminiyle doldurmak exact recovery değildir. Sonuç observable quotient + ambiguity/uncertainty olabilir.
3. **Recovery:** lossy(x) ve witness birlikte x'i geri getiriyorsa witness byte/bit maliyeti hesaplanır. Witness yok veya bozuksa recovery reddedilir.
4. **Authority:** veri üzerindeki `authorized=true` alanı otorite değildir. İzin, ayrı trusted policy state'ten çözülür; modelin outputu grant değildir.
5. **Invariance:** yalnız tanımlanmış dönüşüm ve görev altında korunması gereken özelliğe uygulanır; observer-specific bilgi ayrıca korunur. Tüm temsilleri eşitlemek hedef değildir.

## OCIR v0.1 zorunlu alanları
`schema_version`, `schema_sha256`, `program_id`, `source_sha256`, `module_graph`, `typed_blocks`, `ops`, `operand_types`, `shape_constraints`, `observer_context`, `provenance_refs`, `required_effects`, `limits`, `numeric_policy`, `entrypoint`.

Runtime event: `run_id`, `step`, `op_id`, `input_hash`, `output_hash`, `state_ref`, `effect_request`, `effect_decision`, `recovery_ref`, `error_code`, `clock_mode`. Hash sadece bütünlüktür; doğruluk veya yetki değildir. Replay frozen external responses kullanıyorsa bunu event kaydında belirtir.

## Model ABI / dil→AI bağı
`LanguageContract`: schema hash, token/AST vocab hash, opcode versions, masks, evaluator version, compatible model contract versions. `ModelRequest`: task, typed input/goal, observer/context, available permitted tools, memory ref, resource bound. `ModelProposal`: program/OCIR, predicted state, uncertainty/abstention, cited source IDs; sonradan verifier sonucu ayrı alandır.

Graph subset başlangıcı: matmul, add, elementwise activation, reshape, normalization, softmax ve linear head. Dtype/shape kuralları tip denetleyicide, yürütme explicit host adapter veya VM op registry'de. Training config içindeki graph'ın ICL source/OCIR hash'i kaydedilir; ICL spec'i tamamen bypass eden aynı isimli Python modeline NATIVE_LANGUAGE_BASED etiketi verilmez. Autograd host backend olabilir; bu FFI sınırı açık kalır.

## Önerilen örnek akış (pseudocode; dondurulmuş sözdizimi değildir)
```text
module example
observer left: ObserverSpec
fn project(x: Tensor[2], ctx: Context) -> Result[Representation[Tensor[1]]]
    require compatible(left, ctx)
    return observe(left, x, ctx)
fn recover(y: Representation[Tensor[1]], witness: RecoveryWitness) -> Result[Tensor[2]]
    return recover_exact(y, witness)
```
Astra bunu gerçek EBNF/implementation ile tutarlı `.icl` örneğine dönüştürür. Bu dosyadaki pseudocode'u executable fixture diye saymaz.

## Hata sınıfları
LEX, PARSE, NAME, TYPE, SHAPE, OBSERVER_MISMATCH, FRAME_MISMATCH, NON_IDENTIFIABLE, WITNESS_MISSING, WITNESS_CORRUPT, EFFECT_DENIED, HUMAN_APPROVAL_REQUIRED, FUEL_EXHAUSTED, MEMORY_LIMIT, SCHEMA_INCOMPATIBLE, UNSUPPORTED_OP. Hatanın kaynağı test, model veya runtime ayrı tutulur.

## Sürüm kuralı
v0.1 grammar/token/schema dondurulmadan ana model benchmark'ı başlatılmaz. Semantik değişirse contract major/minor ve dataset lineage güncellenir; eskiler saklanır. Compatibility migration'ın kendisi test edilir. Source-of-truth: https://drive.google.com/drive/folders/1DF-ltZ-cZ0hgituifshgkYonmwGvYYtT
