# ASTRA — OCIL PROGRAMLAMA DİLİ / ICL-CORE YÜRÜTME EMRİ
Sürüm: OCIL-LANG-01 / 2026-10-10-v1 · Hedef: gerçek kod, gerçek test, özel sürümlü Drive teslimi

## 0. Görev ve adlandırma
OCIL/OCIR araştırma programının ilk somut ürününü **Invariant Cognition Language — ICL-Core** olarak geliştir. OCIL'i başka bir OCL standardı/diliyle karıştırma. Bu görev mevcut Invariant Computing çalışmalarının devamıdır; eski kaynakları, frozen deneyleri ve teslimleri silme. Dilin araştırma sahibi OCIL, onu AI ve çalışma ortamı olarak kullanan girişim Invariant OS'tur. İki ayrı dil icat etme.

Bu bir plan yazma görevi değildir. Sözdizimi, tip sistemi, tanımlı yürütme semantiği, OCIR, çalışan compiler/interpreter, standard library, CLI, örnek programlar, testler ve yeniden üretilebilir dağıtım üret. Basit bir JSON wrapper, yedi satırlık sayısal DSL, çalışanmış gibi gösterilen arayüz veya Python'a string eval çağıran kabukla tamamlandı deme. Sürüm küçük olabilir; fakat dil olarak gerçekten program yazdırıp çalıştırmalıdır.

Girdi klasörü: https://drive.google.com/drive/folders/1qJLWNbcYlLwPY9Vl9K9XdjILxKfPK-0B
Ortak kontrol/kaynak dosyaları: https://drive.google.com/drive/folders/1PeRnhCK4gPcJO2QF5A9AaXx_fajvgkdm
Spesifikasyon teslimi: https://drive.google.com/drive/folders/1DF-ltZ-cZ0hgituifshgkYonmwGvYYtT
Test/kanıt teslimi: https://drive.google.com/drive/folders/1mQHs23crqeTzRp3DI_M--E-Rbu5S8tEX
Kaynak kodu ve sürümlü build teslimi: https://drive.google.com/drive/folders/19U1ZAPDKIyJzdutTol2werZjmBy7ls_f

## 1. Önce oku ve kaynak zincirini kur
Ortak klasörde `01_KANONIK_DUZELTME_VE_MVP_SIRASI.md`, `SOURCE_MAP.json`, `KAYNAK_INCELEME_NOTU.md`, `CATALOG_SCAN_RECEIPT.json`, `SELECTED_CATALOG_ROWS.json` ve `ARCHIVE_CONTENT_READS.json` dosyalarının tamamını oku. Ardından `ICL_CORE_TEKNIK_SOZLESME.md` ve `ACCEPTANCE_GATES.json`u aç.

Devam kaydı: https://drive.google.com/file/d/15lBgpNm7UTCCMji7xIZlmDsrz1CRMx4C/view ; durum kaydı: https://drive.google.com/file/d/1E3HgZlJHo-lRLlJ1zCiBVsYB7KvhYoAq/view . V4.0.4 → korunmuş V4.0.3 sırasını koru. Eski geçici `/tmp` dizinleri mevcut varsayılmaz.

Katalog ana klasörü: https://drive.google.com/drive/folders/1cE4POvzQkrhGZeEXEtdyfOaQXKybvL70 . Metadata CSV'lerini veya manifesti doğrulanmış SQLite kataloğunu kullan. 284.934 kaynak satırı ile 265.965 tarihsel Drive kaydı okunmuş dosya/deney sayısı değildir. Ekteki seçki yalnız lexical arama sonuçlarıdır; venv/site kopyalarını özgün çalışma sayma. Önce arşiv üye listesi, sonra gereken metin ve kod. Dosya, arşiv üyesi, hash, sürüm, hak ve son başarılı checkpoint'i kaydet.

OCIL arşivi: https://drive.google.com/file/d/1k8qRZEupQj7qlB7FyS8KS-YoK8gXjlfn/view . Özellikle `var/www/invariantcomputinglab/ocil-ocir/index.html` ve `home/deploy/invariant_nightshift/NS_20261006_V1_3b50afc86d1f/run/reports/manuscripts/OCIL_OCIR_TECHNICAL_DRAFT.md` üyelerini aç. Invariant OS arşivi: https://drive.google.com/file/d/1E3kw6ub4_sxvcXmiBl06GPBxP7q1uGYT/view ; `var/www/invariantcomputinglab/invariant-os/index.html` ve gerçekte ulaşılabilen Trace Kernel kodlarını bul. HTML demo açıklaması kaynak kodunun yerine geçmez.

MLGT ana metin: https://drive.google.com/file/d/16NHI_NwjcxiHuOyOGrclBcmqqai8U48-/view . Proof eki: https://drive.google.com/file/d/1dIoC0hr0lCml4LDQKrq1MrP6fQx3F9Kr/view . GPNT, DCT, SFT ve diğer tarihsel başlıkların tam bağlantıları SOURCE_MAP'tedir. “Tüm çalışmalarımızdan yararlan” talimatını her şeyi indiscriminately eğitime almak diye yorumlama: bütün ailelere uygulanabilirlik kararı ver, uygun olanı kaynak/fonksiyon/test ile bağla, diğerlerini gerekçesiyle ayır.

Katalogda bulunan daha eski gerçek parser/compiler/MLG/ICL kodlarını öncelikle incele. Kullanılabilir özgün kod varsa ayrı çalışma dalında genişlet; yoksa `NEW_IMPLEMENTATION` olarak kodla. Yeni tasarımı eski araştırmanın kanıtlanmış sonucu diye sunma. Yeni P0 dil hedefine rağmen özgünlük iddiasını sırf ad değişikliğine dayandırma.

## 2. Araştırmadan dile gerçek aktarım
OCIL: gözlemci, filtre, bağlam, temsil ve provenance dilin taşınan tip/metadata sözleşmesidir. RARI: tanımlanabilirlik, ortak gözlenebilir altuzay, yanlış eşleme ve aile-dışı sınırlar referans testlerinin dayanağıdır. AFC: geri kazanım ancak gerekli durum/yan bilgi saklandığında exact olabilir; irreversible işlemlerde kaybı gizleme. SACRA: yetki, kaynak ve insan onayı açık effect/capability kapısıdır. IEVF: program→run→test→iddia izini saklayan kanıt formatıdır. GOP: evrensel fizik motoru değil, gauge/tolerans/bellek karşı-örnekleriyle yanlış aşırı iddiaları sınırlayan test kaynağıdır.

MLGT'nin kompozisyon/bağlam/çoklu temsil hedefini somut program sözleşmesine çevir. GPNT/DCT/SFT fonetik/geometrik eşlemeleri önce isteğe bağlı kütüphane/deney modülü olarak ele al; kesin aritmetiğin yerine doğrulanmamış işlem tanımı koyma. Kaynaklarda bozuk sembol varsa sayfa görüntüsünü kontrol et; çözülemeyeni tahminle tamamlama. “Evrensel dil anlama”, “sonsuz entropinin kayıpsız sıkıştırılması”, “bilişsel yük %90 azaldı” gibi iddialar compiler kabul koşulu değildir.

## 3. ICL v0.1 dil çekirdeğini dondur
Önce küçük fakat tamamlanabilir RFC yaz; hangi parça kaynakta, hangisi yeni öneri belirt. EBNF grameri, lexing/Unicode kuralları, öncelik/associativity, lexical scope, import çözümü, entrypoint ve hata kodlarını tanımla. `Bool`, checked signed `Int64`, `Float64`, `String`, `List<T>`, kayıt/tuple, `Option/Result`, fonksiyon ve şekli belirtilmiş küçük tensor/matrix tipi kapsansın. Branch, kullanıcı fonksiyonu, modül, yerel bağlama ve bütçeli döngü/recursion çalışsın. Daha geniş sayı/generics/async sistemi sonraki sürüm olabilir; eksik özellikleri açıkça ver.

`Observer`, `Context`, `Representation<T>`, `ProvenanceRef`, `RecoveryWitness`, `Capability` ayrımını taşı. Float hata toleransı, overflow, bölme-sıfır, NaN/Inf, shape mismatch ve kaynak limitinin semantiği açık olsun. `Exact<T>` ve `Approx<T, error_bound>` veya eşdeğer açık result ayrımı kullan. Serileştirme round-trip'i ile kayıplı ölçümden kaynak kurtarmayı aynı test sayma.

Type-and-effect checker; gözlemci/frame/unit uyuşmazlığını örtülü cast ile geçmesin. Dönüşüm açık kaynak/protokol ile istenir. Kanıtlanamayan önkoşulda `Unknown/NeedsEvidence` üret; yapay güvenlik sertifikası verme. Type safety iddiası yalnız tanımlı alt dil ve gösterilen ispat/test kapsamındadır.

## 4. Gerçek toolchain'i kodla
Pipeline: kaynak `.icl` → token/source-span → AST → name/type/effect check → typed OCIR → bytecode → VM. Bağımsız ağaç-yorumlayıcıyı semantik oracle olarak yaz veya uygun mevcut uygulamayı kaynakla benimse. Yorumlayıcı ile VM aynı yürütme fonksiyonunu çağırıp bağımsızlık taklidi yapmasın. Ortak parser kullanabilirler; yürütme implementasyonları ayrı olsun. Hatalar stdout başarı çıktısına karışmasın; makine okunur JSON ve insan okunur diagnostics üret.

OCIR sürüm, feature set, source SHA, bağlam, observer map, typed operations, effects ve schema hash taşısın. Canonical serialization/hash ve sürüm uyumsuzluğu hatası olsun. Bilinmeyen opcode ve zararlı payload fail-closed çalışsın. İleride LLVM/WASM backend eklenebilir; ilk kabul için native codegen/FPGA şart değil. Host Python/Rust/C++ kullanmak kabul edilir; yeni dilin sözdizimi ve semantiği bağımsız tanımlanmalıdır.

İlk CLI hedefleri: `icl check`, `icl run`, `icl compile`, `icl inspect`, `icl replay`, `icl test`. Bunlar geliştireceğin arayüz sözleşmesidir; bugün varmış gibi deneme komutu yazma. Desteklenen her altkomut için `--help`, exit code, machine-readable output ve test ekle. Installable package/lockfile ve temiz ortam kurulumu üret. Ağsız örnekler ilk çalışmada doğrulansın.

## 5. Recovery, observer ve güvenlik davranışı
Deterministik sonlu çekirdekte kesinti/checkpoint/replay aynı sonucu üretsin; PRNG durumunu da kayıtla. External effect geri alınması ile yerel journal rollback farklıdır: gönderilmiş e-posta, dış API veya fiziksel eylemi “geri alındı” ilan etme. Varsayılan FFI, ağ, dosya yazma, shell ve dinamik yükleme kapalıdır. Yetkili eylemler açık capability ve gerekirse insan onayıyla ayrı adapter üzerinden geçsin; model capability üretemesin.

Fuel/step, bellek, stack, tensor boyutu ve çıktı limitleri uygula. `eval/exec`, path traversal, symlink, arşiv extraction bomb, import cycle, Unicode görünmez karakter ve serialization saldırı testleri yaz. Runtime'i üretim düzeyi sandbox diye adlandırmak için ilgili izolasyon testleri gerekir; v0.1 için sınırı açıkça etiketle.

Aynı ölçümü üreten iki farklı kaynak, kayıpsız kurtarma iddiasını bozmalı. x=1 ve x=257'nin mod-256 collision'ı gibi sonlu karşı-örnekleri kullan; side-information eklenmedikçe kaynak tekil sayılmasın. Tek/iki gözlemci ve rank-deficient gözlem örneklerinde yalnız tanımlanabilir bölüm için başarı raporla. Wrong pairing ve nonlinear out-of-family örnekleri başarısızlığı görünür kılsın.

## 6. AI modeline verilecek çalışır temel
Model ekibine sadece metin sözlük verme. Dondurulmuş OCIR schema/token vocab, program AST canonicalizer, bağımsız interpreter oracle, transition/state formatı, izinli action şeması ve checkpoint API ver. Eğitim örneği programı gerçekten derlenip yürütülmüş olmalı. `program`, `input_state`, `observer_context`, `output_state`, `effects`, `trace`, `expected_error`, `recovery_witness`, `source_lineage` alanları kesin olsun.

ICL içinde model/graph tanımlamak için doğrulanabilir bir modül sözleşmesi kur: tensor op registry ve açık typed FFI sınırı. Küçük bir forward grafiği ICL/OCIR'den host backend'e derlenip bağımsız referansla karşılaştırılsın. Böylece “model dilin temelinden” iddiası sadece eğitim promptunda ICL adının geçmesine dayanmaz. Tüm CUDA/autograd altyapısını sıfırdan yazmak ilk sürümün şartı değildir; host sınırını belgede açıkça göster.

## 7. Kabul bataryası — kapılar başarılana kadar genişlet
Ortak ACCEPTANCE_GATES'teki sayılar yeni mühendislik hedefleridir, gerçekleşmiş sonuç değildir. En az 40 anlamlı valid/invalid program ve 1.000 seed'li generated differential case oluştur. Tek aritmetik işlemin bin tekrarını bin semantik test sayma. Modül/fonksiyon/branch/loop/record/tensor/observer/recovery/effect ailelerini ayrı kapsa. En az 30 adversarial vaka: type, provenance, capability, corruption ve kaynak aşımı. Beklenen hatalar da başarılı test olabilir; hata alan ürünü çalışır model diye etiketleme.

Girdi→parse→pretty-print→parse AST eşdeğerliği; interpreter↔VM sonuç/hata/effect parity; OCIR canonical round-trip; checksum bozulması; kesinti/restart; izin reddi; 8 küçük tensor-forward grafiğinde bağımsız host parity; offline kurulum ve E2E CLI testlerini çalıştır. Exact domain'de fark sıfır, Float64 referans testinde önceden konmuş atol/rtol; toleransı sonucu gördükten sonra gevşetme. Yeni tolerance kararı yeni protokol sürümüdür.

En az 6 gerçek demo: gözlemci-koşullu temsil, collision+sideinfo, frame dönüşümü, kaynak/yetki çatışması, checkpoint replay ve küçük model forward grafiği. Klinik veri kullanma; biyomedikal demo ancak açıkça sentetik. Demo video/UI testin yerine geçmez.

## 8. Teslim, kanıt ve devam
`LANGUAGE_SPEC.md`, `grammar.ebnf`, `OCIR_SCHEMA.json`, `TOKEN_VOCAB.json`, `SEMANTICS.md`, `SECURITY_BOUNDARY.md`, package kaynak ZIP'i, örnek `.icl` programlar, `requirements/lockfile`, bağımsız runner'lar, `TEST_RESULTS.json`, ham loglar, `SCIENCE_TO_CODE_TRACE.json`, `CHANGELOG.md`, `MANIFEST.json`, `RESUME.json` teslim et. Her iddia source hash→source member→design decision→code symbol→test bağı taşısın.

Drive'a yeni sürüm yaz; manifest/hash ve yeniden okuma kontrolü yap. `SPEC_DRAFT`, `IMPLEMENTED_NOT_TESTED`, `CONFORMANCE_PASSED`, `RESEARCH_NOT_REPRODUCED`, `BLOCKED` durumlarını ayır. `CONFORMANCE_PASSED`, evrensel dil teorisinin veya AI yeteneğinin kanıtı değildir. Eksik bağımlılık varsa gerçek hata/son komut/sonraki komutu kaydet; sadece komut belgesi üretip işi bitti sayma. Mevcut olmayan bir worker veya arka plan işi uydurma.

Önce ilk çalışan semantik alt dilini bitir; schema/hash'i dondur; Invariant OS komutuna `LANGUAGE_HANDOFF.json` ile aktar. OCIR değişirse eğitim verisi/model sürümü de yeni schema hash ile yeniden değerlendirilir. Kamu GitHub/HF yayını, cloud harcaması, hasta verisi erişimi, canlı VPS ve frozen bankalara müdahale bu görevin otomatik yetkisi değildir.

**Şimdi yürüt:** kaynak zincirini aç → gerçek eski kodu doğrula → eksik gramer/semantiği implement et → interpreter/VM fark testlerini çalıştır → modelin kullanacağı OCIR ve forward sözleşmesini doğrula → somut kod/test/hand-off dosyalarını belirtilen Drive klasörlerine kaydet.
