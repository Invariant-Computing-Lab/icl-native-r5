# ASTRA — INVARIANT OS / INVARIANT COGNITION LANGUAGE VE ICL-NATIVE AI
Sürüm: IOS-ICL-01 / 2026-10-10-v1 · Birinci MVP · Gerçek eğitim ve tekrar yüklenebilir model hedefi

## 0. Asıl ürün
Invariant OS'un birinci MVP'sini **Invariant Cognition Language** olarak üret. AI bileşeni **ICL-Native** olsun: OCIL'in ICL-Core/OCIR semantiğine dayalı, typed program/durum dönüşümlerini öğrenen, bağlam ve gözlemciyi açık taşıyan gerçek parametreli model. Genel bir chatbot kabuğu, yalnız RAG, API yönlendirici, arşiv metinlerini özetleyen panel veya hazır modeli yeniden adlandırmak bu teslim değildir.

OCIL araştırma programı dilin/OCIR'nin sahibidir; Invariant OS aynı core'u kullanan girişimdir. Önce `ASTRA_01_OCIL_PROGRAMLAMA_DILI.md` sözleşmesini çalıştır veya üretilmiş doğrulanabilir handoff'u kullan. İki ayrı ICL grameri üretme. Model kodunu, mümkün olan semantic graph katmanında ICL tanımlarından derle; host tensor/autograd backend sınırını açık göster. İlk sürüm küçük olabilir ama öğrenme, kayıt, yeniden yükleme ve tutulmuş örnekte inference gerçekten gerçekleşmelidir.

Model/ürün klasörü: https://drive.google.com/drive/folders/1GrIl1-lnseiDauvFwS-tWRR0ALfQLxHF
Model ve eğitim: https://drive.google.com/drive/folders/162HhobtZ4nRDExFSMPbXNhNMV-Qj-_FP
Veri ve değerlendirme: https://drive.google.com/drive/folders/1mpjnN7QVbsxeqS4FMb4rXQZWXPRSpP57
Kaynak/ağırlık/build teslimi: https://drive.google.com/drive/folders/1d7U_FHbE7m0K5kpveHnOtHZTPhTa-6EP
Dil kaynağı: https://drive.google.com/drive/folders/1qJLWNbcYlLwPY9Vl9K9XdjILxKfPK-0B
Ortak kaynak ve yeni öncelik: https://drive.google.com/drive/folders/1PeRnhCK4gPcJO2QF5A9AaXx_fajvgkdm

## 1. Başlangıç ve korunacak işler
`01_KANONIK_DUZELTME_VE_MVP_SIRASI.md`, `SOURCE_MAP.json`, `KAYNAK_INCELEME_NOTU.md`, `ICL_CORE_TEKNIK_SOZLESME.md`, `ICL_NATIVE_MODEL_EGITIM_PROTOKOLU.md`, `ACCEPTANCE_GATES.json`, en güncel V4.0.4 handoff ve gerçek eski source ZIP'lerini aç. Dil için compiler/evaluator/schema/token hash'leriyle `LANGUAGE_HANDOFF.json` yoksa veri şeması hazırlığı yapılabilir, fakat dil tabanlı model kabulü verilemez.

G51 Runtime Console kaynak ve AFC recovery katkısı korunarak ICL runtime/provenance/replay bileşeni olur. G52 ISC16 Developer Workbench ve G53 RTL kiti destekleyici hat olarak kalır; eski testler ayrı. V4.0.4 sonrası bu iki alanın P0 hedefi ICL'dir. Diğer 18 tarihsel ürün hattını silme veya tamamlandı sayma. Klinik, canlı servis ve frozen deney kuralları değişmez.

## 2. Ekteki 10 HF ailesini doğru kullan
SOURCE_MAP'teki M01–M10 kayıtlarının her biri için `uri`, gerçek artifact türü, loader, config, weights/tensor names, preprocess/tokenizer, license/rights, source SHA, read status, provenance ve kullanılma biçimini kayıtla. Etiketinde “model” yazması ağırlık varlığının kanıtı değildir.

M01 NeuroBrain / M02 observer-filter: uygun gerçek estimator/parametre bulunursa yalnız kapsamı tanımlı observer reconstruction öğretmeni/oracle/baseline adayıdır; metin üretim LLM'i olarak birleştirme. M03 GOP G6: sınırlı karşılaştırıcı ve negatif/kapsam testi; genel AI temeli diye yükseltme. M04/M05 MRI/HuReT: aynı kaynak linki iki bağımsız checkpoint'i kanıtlamaz; model/dataset/domain adapters ayrı incelenir. MRI ham klinik veri ilk core eğitime girmez.

M06 RhythmWalk ve M07 NCL: zaman serisi/domain transfer için sonraki adapter/baseline adaylarıdır. M07'nin dizindeki bağlantısı `ncl_synthetic_dataset.csv`dir; bu ağırlık değil. M08 bounded policy: gerçek source bulunursa capability/action/recovery sözleşmesine kaynak; policy ağı modelin trusted izin kapısı olamaz.

M09 RouterKey ve M10 Offline GLM aynı key-only rapora bağlıdır: https://drive.google.com/file/d/1yhiYJktJKxFMqco5Dp8RwT18j9jZSrJd/view . Raporun tam model forward çalıştırmadığını, PGK/routing fidelity ile LRU'ya karşı negatif transfer sonucunu koru. Routing codec tek başına neural checkpoint değildir. GLM/Kimi/Qwen gibi üçüncü taraf kaynaklar bulunursa kimlik/lisans/commit/hash ile baseline, teacher veya isteğe bağlı frontend olarak değerlendir; bizim sıfırdan eğitilmiş modelimiz diye adlandırma. Mimarileri/tokenizerları uyuşmayan ağırlıkları adlarına göre merge etme.

## 3. Ayrı model yolları, tek ana hedef
**NATIVE_FROM_SCRATCH:** ICL/OCIR için kendi token/typed-graph/state arayüzümüz, kendi trainable modüllerimiz ve random initialization ile gerçekten eğitilmiş checkpoint. Bu görevde zorunlu ana araştırma yoludur; model küçük olsa da gerçek olmalı. Önceden var olan uygun özgün ICL ağırlığı keşfedilirse doğrula, korunmuş warm-start deneyini ayrı `ORIGINAL_CONTINUATION` olarak yürüt; from-scratch iddiasına karıştırma.

**THIRD_PARTY_ADAPTER:** Gerekçeli ve izinli küçük bir açık model üstüne ICL instruction/AST adapter. Yardımcı kıyas/ürün yolu; native çekirdeği ikame etmez. GPU/ağırlık yoksa bu yol `NOT_RUN` kalabilir; küçük native eğitimi buna bağlayıp durma. Büyük GLM/Kimi modeli yüklenmedi diye ICL language-core eğitimini yapmamak kabul edilmez.

**COMPOSED_SYSTEM:** Native semantic core + optional doğal dil frontend + deterministik verifier/runtime. Sistem çıktısındaki başarı; native model, frontend, search ve verifier katkıları ayrı ölçülerek raporlanır. Yeni sıfırdan model, fine-tune, weightless codec ve ürün sistemi dört ayrı varlıktır.

## 4. Dilden gelen model mimarisini kodla
Başlangıç önerisi: typed OCIR node/op encoder, observer/context encoder, durum/geçiş belleği ve action/program decoder. AST edges/scope/types ile temsil öğren; output vocabulary dondurulmuş opcode/type contract'tan gelsin. Task-preserving canonical state ile observer-specific state ayrı taşınsın. Her gözlemciyi körlemesine tek latent vektöre çökertme. Önce trainable iki küçük ablation-compatible modeli çalışır kıl; sonra daha büyük kapasite seç.

Model hedefleri: ICL/OCIR program üretme ve tamamlama; derleyici hatası onarma; input+programdan state/effect tahmin etme; tanımlı observer dönüşümünde görev sonucunu koruma; context değişince gerektiğinde farklı davranma; eksik gözlemde bilinemez/abstain çıktısı; sınırlı belleğe dayalı çok-adımlı görev. Executor gerçek typed proposal'ı alır, check/effect/recovery kapılarını bağımsız işletir. Program trace'i gözlenebilir işlem kaydıdır; modelin iç muhakemesinin veya bilincinin kaydı gibi sunulmaz.

Graph/layer tanımı `model.icl` veya dondurulmuş ICL graph modülünden typed OCIR'ye indirgensin. İlk host backend PyTorch olabilir. En az bir gerçek forward grafiğinde ICL→OCIR→backend ile bağımsız reference sonuçları ve gradient yolu karşılaştırılsın; tüm modelin hangi katmanının host'ta kaldığı belgelenir. Böylece dil modelin token data'sında, architecture ABI'sinde, execution'ında ve değerlendirmesinde izlenebilir rol taşır.

## 5. Eğitim verisini üret; kaynakları ezber deposuna çevirmeme
İlk dataset izinli sentetik program/observer/state aileleri ve açık kaynaklı, lisansı doğrulanmış örneklerdir. OCIL compiler/reference interpreter programları çalıştırıp output/trace/error etiketi üretir. Güvenli kurum içi araştırma metinleri ayrı kaynaklı retrieval collection olabilir; model eğitimi ve RAG aynı işlem değildir. 66 GB aktarıldı diye hepsi eğitime alınmaz.

D22 OCIL pairs'i program+AST+OCIR+input/output+trace+context+observer+validity corpus'una genişlet. D23 SACRA authority çatışmaları ve D24 IEVF claim gate ayrı alt görevlerdir. D04/05/07/09 RARI ve D12 AFC'den uygun kontratlı sentetik aileler; D11 GOP'tan negatif ve bellek karşı-örnekleri ekle. Kapalı/repeat/test bankaları, hasta/EDF/DICOM ham verileri, özel anahtarlar ve izni belirsiz lisanslı eserler eğitim dışında kalır. D14–D18 yalnız izin ve domain kararı sonrası ayrı adapter çalışmasıdır. NCL15.750 satırı insan beyin kanıtı değildir.

Her örnek `example_id`, `family_id`, `canonical_program_id`, `semantic_group_id`, `observer_orbit_id`, `source_artifact`, `generator_version`, `seed`, `rights`, `schema_hash`, `split` taşısın. Programın yüzeysel variable-renaming/whitespace varyantları farklı splitlere sızmasın. Observer çiftleri ve aynı latent dünyanın türevleri grup olarak ayrılsın. Önce split manifestini dondur, sonra teacher/synthetic generation ve augmentation uygula. Eğitimde held-out outcome, test-specific primitive veya evaluator response bulunmasın.

İlk smoke corpus'u küçük, proof-of-pipeline olarak etiketli olsun. Ana research run için protokoldeki >=20.000 train, >=2.000 validation, >=2.000 ID-test ve >=2.000 structural/OOD hedefini yalnız gerçek benzersiz semantik gruplarla karşıla. Çeşitlilik bu sayıları sağlamıyorsa tekrarla doldurma; gerçek sayıyı raporla. Veri miktarı başarı garantisi değildir.

## 6. Kayıp fonksiyonları ve eğitim
ICL syntax/op-token loss; state-transition loss; compiler/oracle trace supervision; yalnız geçerli transformation pair'lerinde task/quotient invariance veya equivariance loss; yanlış eşleme ve task-distinct çiftlerde contrastive negative loss; ambiguity/abstention supervision. Tüm katsayılar validation'da seçilir. Invariance loss'u farklı anlamları birbirine zorlamasın. Encoder collapse'ı embedding variance, rank ve downstream task ile kontrol et.

Interpreter normalde differentiable değildir. Executor doğruluğunu doğrudan gradient loss gibi yazma: ya doğrulanmış target trace CE, ya açık differentiable numeric subset, ya da ayrı tanımlı policy/reward yöntemi kullan; gradient gerçekten akıyor mu test et. Verifier'in reject mask'i veya policy gateway modelin kendi öğrenme başarısı değildir. Raw proposal ve accepted proposal skorlarını ayrı sakla.

Training loop gerçek optimizer update, initial/final weight hashes, parametre sayımı, loss curve, seeds, hardware, time/memory, config, checkpoint ve resume içersin. Minik veri overfit testi yalnız wiring testi. Ana benchmark en az üç bağımsız seed'le yapılır; aynı checkpoint'in üç kere ölçümü üç seed değildir. Mixed precision/nondeterminism/CPU-GPU parity sınırlarını belirt. Optimizer, RNG, scheduler, step ve dataset position checkpoint'i korunsun. Numeric toleranslar ve eval generator hash'leri sonuçlardan önce sabitlenir.

## 7. Donanım ve bütçe gerçeği
CPU/RAM/disk/GPU/VRAM'i gerçekten ölç. `SMOKE_CPU` en küçük model ve birkaç yüz/az bin örnekle training-save-load-inference kablajını tamamlasın; model boyunu mevcut RAM'e göre ayarla. `RESEARCH_LOCAL` onaylı mevcut kaynağa sığacak ölçekte çalışsın. `SCALE_GPU` ancak kaynak mevcut ve harcama yetkisi açık olduğunda yürüsün. Parameter profile'ları örneğin 1–5M smoke ve 10–50M araştırma aralığı olabilir; bunlar sabit donanım garantisi değil, profil önerileridir. Ölçülen parametre sayısı ve kaynak kullanımı kaydedilir.

GPU gerekçesiyle devasa temel model sipariş etme, ücretli servis açma veya kota aşma. Kaynak yetmiyorsa küçük gerçek native checkpoint teslim et ve büyük run'ı `BLOCKED_RESOURCE` olarak bırak. Günler sürecek işi araç gerçekten çalıştırmıyorsa arka planda sürdüğünü söyleme.

## 8. Baseline, ablation ve kabul
Baseline'lar: non-learning majority/lookup; aynı corpus, benzer parametre ve compute ile plain token model; varsa izinli third-party baseline. Deterministik executor semantic oracle'dır, her neural modelin “yenmesi gereken” zeka rakibi değildir. Task metric'leri: raw syntax/type validity, execution exact match/pass@1, semantic equivalence, state RMSE, observer transfer, wrong-pair/out-of-family rejection, recovery correctness, selective risk+coverage, permission violation attempts/executions, latency ve bellek.

Ablation: observer/context encoder yok; invariance objective yok; typed-graph yerine flat tokens; state memory yok; recovery witness yok; learned policy yerine dış gate etkisini ayrı karşılaştır. Ana modelde policy kapısını kapatarak gerçek yetkisiz eylem yapma: gate ablation yalnız izole simülasyonda. Değişmeyen compute/data/eval koşulları tutulur. Güven aralıkları örnek değil semantik aile/grup bootstrap'ına dayanır; subgroup ve en kötü aile skorları görünür olsun.

Protokolde önceden yazılmış pilot yeterlilik kapıları ile üstünlük iddiası kapısını ayır. Baseline'dan üstünlük kurulmazsa sonuç negatif/inconclusive olur; modeli silme veya eşikleri sonradan kaydırma. Sadece verifier kabul ettiği çok az örneğe bakıp yüzde100 başarı deme; tüm girişler üstündeki pass@1 ve kabul coverage zorunludur.

## 9. Model paketi ve offline gerçek inference
`model.icl`, compiled OCIR, configuration/modeling code, tokenizer/vocab, `model.safetensors` veya güvenli loader'lı parametre biçimi, manifest/hash, training config, split/generator registry, evaluation runner, raw outputs ve model card üret. Model card base_model=null(from-scratch) veya gerçek third-party id(revision) ayrımını, corpus provenance ve scope'u doğru yazsın. Dosya adına safetensors yazmak yeterli değildir; loader gerçek dosyayı açmalıdır.

Tamamen yeni süreçte, gizli training nesnesi bellekte kalmadan checkpoint yükle; sabit örnekte logits/output parity ve gerçek held-out inference göster. Önceden indirilmiş bağımlılıklarla ağ kapalı test yap; görünmez API fallback yasak. Quantization/GGUF export ancak mimari/backend destekliyorsa ayrıca tested olur; her yeni modelin otomatik GGUF desteklediğini varsayma. Üçüncü taraf remote code varsayılan kapalı; gerekli ise kod inceleme+commit pin şart.

Demo CLI/arayüz ancak model+executor gerçekten çalışınca hazır sayılır. Model load/replay, graph inspection, typed errors, evidence/source paneli ve yetki kararları gösterilsin. Model olmayan modda `MODEL_NOT_LOADED` göster; sabit cevabı inference diye kullanma.

## 10. Son teslim ve doğru statü
`MODEL_CARD.md`, `TRAINING_REPORT.md`, `EVAL_REPORT.md`, `NEGATIVE_FINDINGS.md`, `ABLATIONS.json`, `DATA_MANIFEST.json`, `LANGUAGE_DEPENDENCY.json`, `MODEL_LINEAGE.json`, weights/code ZIP, checkpoint, gerçek komut/loglar, `TEST_RESULTS.json`, `REPRODUCE.md`, `RESUME.json` ve `NEXT_ACTION.md` özel Drive'a sürümlü kaydedilsin. Manifest, dosya boyutu, hash ve uzak yeniden okuma doğrulansın. GitHub/HF içerikleri hazırlanır fakat kullanıcı ayrıca yetki vermeden kamuya yayınlanmaz.

Statüleri ayır: `MODEL_SPEC_ONLY`, `TRAINING_STARTED`, `SMOKE_TRAINED`, `RELOAD_VERIFIED`, `PILOT_TASK_QUALIFIED`, `BENCHMARK_INCONCLUSIVE`, `NATIVE_MODEL_RESEARCH_READY`, `PUBLICATION_NOT_AUTHORIZED`. Smoke eğitimi genel AI, bilinç, klinik başarı veya daha önceki teorilerin doğrulaması değildir. Mimari yeniliği, mevcut neural bileşenleri kullanan yeni sistem tasarımıyla karıştırma; prior-art incelemesi ayrı gerekir.

**Şimdi yürüt:** OCIL language handoff'u doğrula → 10 HF ailesinin gerçek artifact rollerini belirle → program/veri/split generator'ını çalıştır → küçük gerçek ICL-native modelini eğit → checkpoint'i yeni süreçte yükle → held-out ve ablation testlerini uygula → başarısızlıkları da içeren kod/ağırlık/kanıt paketini Drive'a kaydet. Sadece bu emri tekrar yazıp bitirme.
