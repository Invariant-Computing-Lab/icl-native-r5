# ICL-Native / eğitim ve değerlendirme protokolü
10 Ekim 2026 · Önerilen deney protokolü v1 · Bütün sonuçlar başlangıçta NOT_RUN

## Hedef ve falsifiye edilebilir soru
ICL/OCIR'deki açık observer/context/type/state yapısını kullanan trainable model, eşleştirilmiş flat-token baseline'a göre yeni program bileşimlerinde ve observer değişiminde görev doğruluğunu iyileştiriyor mu? Kaynak metinlerin doğrudan ileri sürdüğü kanıtlanmış sonuç değil, bu görevde sınanacak mühendislik/araştırma sorusudur.

Ana karşılaştırma: ICL-native vs aynı train split, parametre sayısı ±%10 ve gerçek eğitim compute bütçesi ±%10 içinde flat-token model. Bütçe eşleşmesi sağlanmazsa bunu exploratory etiketle. Üç seed, aynı dondurulmuş split; validation seçim protokolü kayıtlı. Oracle interpreter, modelin üretmesi gereken ground truth'u sağlar; başarısı model öğrenmesi değildir.

## Görev aileleri
A: aritmetik, branch, loops, fonksiyon bileşimi, scope/record/tensor shape.
B: observer değişimi, ortak observable quotient, rank-deficiency, yanlış eşleme, family shift.
C: loss+sideinfo exact recovery, eksik/bozuk witness, restart ve reduced-state memory.
D: spatial frame dönüşümü, belge/agent-state, provenance ve authority conflict.
E: derleyici hatası onarma ve küçük graph-to-backend forward parity.
Her aile için pozitif, negatif ve değerlendirme dışı alt durumlar açıkça seçilir. Biyomedikal şema varsa yalnız sentetik adapter deneyidir; klinik doğrulama olmaz.

## Veri ve sızıntı sınırı
Temel örnek alanları: `example_id,family_id,canonical_program_id,semantic_group_id,observer_orbit_id,world_id,source_id,generator_sha,schema_sha,seed,rights,split,program,input,context,expected_output,expected_error,trace`.

Önce canonical AST ve semantic/world/orbit ilişkileriyle connected grouping; sonra train/validation/test ayrımı. Literal değişimi, renaming ve observer varyantlarının aynı semantik kökten geldiği yerde grup aynı splitte kalır. Train-only augmentation sonrası exact hash ve approximate code similarity denetimi yapılır. Test generator seed'leri eğitim/teacher süreçlerine verilmez. Test labels ayrı evaluator tarafından tutulur. Train set'te olmayan daha uzun AST, yeni bileşim ve yeni observer family'leri OOD olarak önceden belirlenir.

SMOKE: küçük gerçek dataset ve optimizer run; içerik miktarı/başarı iddiası sınırı raporlanır. RESEARCH hedefi: 20.000 train, 2.000 validation, 2.000 ID test, 2.000 structural/OOD test; minimum 8 anlamlı alt aile. Bunlar hedef satır sayılarıdır; gerçek benzersiz grup sayısı ayrıca raporlanır. Yetersiz çeşitlilikte tekrarlı örneklerle sayı doldurmak yasak.

## Başlangıç model sözleşmesi
Typed node+op embeddings, observer/context encoder, explicit recurrent state veya state memory, program/action decoder ve ambiguity head. Çekirdek sözleşmeyi `model.icl`→OCIR ile ifade et; PyTorch tensor/autograd host olabilir. Katman/graph varyantları dondurulmuş config içindedir. Şekil/dtype kuralları ve vocab hash'i loader tarafından kontrol edilir. Simetrinin korunacağı latent alt parça ile bağlama duyarlı alt parça ayrılır.

Örnek hedef: `L = L_program + λs L_state + λt L_trace + λi L_invariant + λn L_negative + λa L_abstain`.
Bu denklem proje önerisidir. Kayıpların ölçüm birimi/normalizasyonu, active mask'i, family ağırlığı ve λ seçimi validation protokolünde yazılır. `L_invariant` sadece görev eşdeğeri doğru çiftlerde uygulanır. Anti-collapse varyans/rank kontrolü ve task-distinct negatif çiftler şarttır. Non-differentiable executor için sahte gradient yoktur: denetimli trace veya açık tanımlı ayrı öğrenme yöntemi kullanılır.

## Önceden belirlenmiş kapılar
**Pipeline:** optimizer update sonrası weight hash değişmesi; finite loss/gradient; kaydet→yeni process→yükle→aynı fixture çıktısı; schema mismatch/weight corruption reddi; ağ kapalı inference. Bunlar öğrenilmiş genel yetenek kanıtı değildir.

**Pilot görev yeterliliği (yeni mühendislik hedefleri):** raw syntax validity >=%95; tanımlı ID programlarda raw execution pass@1 >=%80; verifier sonrasında kabul edilen programlarda type/effect conformance %100; authority test paketinde yetkisiz gerçek execution 0; acceptance coverage ve tüm girişler üstü başarı birlikte raporlanır. Bu hedefler karşılanmadıysa `SMOKE_TRAINED/RELOAD_VERIFIED` statüsü korunabilir ama `PILOT_TASK_QUALIFIED` kullanılamaz. OOD için bu turda keyfi %80 şartı yoktur; tam dağılım ve baseline farkı raporlanır.

**Araştırma iddiası:** ana önkayıtlı structural/OOD görevinde grouped-bootstrap %95 güven aralığının baseline'a göre farkı 0'ın üstünde olmalı. Observer+invariance contribution, eşlenmiş ablation ile ayrıca gösterilmeli. Negatif veya belirsiz sonuç `BENCHMARK_INCONCLUSIVE` olarak saklanır. Çoklu yardımcı endpoint'ler ikincil/exploratory; seçim ve düzeltme yöntemi kayıtlı. Test sonuçlarına bakarak benchmark, seed veya λ seçme.

## Ölçümler
Her seed/aile için raw parse/type pass, execution exact match, AST/OCIR semantic match, state RMSE, equivariance/task preservation, ambiguous example false confidence, selective risk vs coverage, semantic memory görevleri, rejection reason, recovery success, illegal attempts ve actual illegal execution sayısı, tokens/steps/latency/peak RAM. Üstünlük yalnız aynı search budget altında karşılaştırılır; rerank/verifier/corrective retries ayrı kolon.

## Ablation ve negatif kontroller
Observer/context yok; invariant objective yok; typed-graph yok; recurrent memory yok; witness yok; doğru eşleme yerine permütasyon. Yetki kapısı dış trusted modüldür; kapısız variant sadece simülasyonda ölçülür. RARI out-of-family, GOP gain ambiguity ve reduced-memory, AFC collision örnekleri başarıya dönüştürülmez. Recovery memory maliyeti ve ek context byte'ları toplam maliyete girer.

## Reproducibility ve yayın ayrımı
Config, seed, Python/framework versions, code commit, schema/vocab/data/eval hashes, host adapter, hardware, optimizer, checkpoint/restart testi, raw logs ve evaluator outputs birlikte teslim edilir. Platformlar arası bitwise determinism varsayılmaz. Model card yalnız gerçek deneyleri içerir. ICL-native tek ürünün bileşenidir; her ablation ayrı “yeni model ailesi” sayılmaz. Public HF/GitHub release ayrı insan kararıdır.

Dış uygulama belgeleri (OCIL'in bilimsel dayanağı değildir):
- HF custom model/config/save-load: https://github.com/huggingface/transformers/blob/main/docs/source/en/custom_models.md
- HF model loading: https://huggingface.co/docs/transformers/main_classes/model
- PyTorch reproducibility: https://github.com/pytorch/docs/blob/site/main/notes/randomness.md
- LLVM language frontend örneği: https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/
Belgeler 10 Ekim 2026'da çevrimiçi kontrol edildi. Astra kurulumda kullandığı somut sürümleri tekrar doğrulayıp pinlemelidir. Bu kaynaklardan birinin tutorial kodu ICL'nin özgün araştırması diye etiketlenmez.
