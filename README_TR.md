# Invariant Cognition Language — R5 yerel çalışma paketi

OCIL-Core 0.2.1, sıfırdan eğitilmiş sınırlı native model ve yerel Invariant OS araştırma konsolu. Genel sohbet modeli veya onaylı 18 görevin tamamlandığı bir nihai ürün değildir. Önce MODEL_CARD.md ve CURRENT_STATUS.json okunmalıdır.

## Kurulumsuz yerel deneme
ZIP'i bir klasöre çıkarın. Python 3.11 veya üzeri yeterlidir; bu iki komut için PyTorch, NumPy, GPU veya internet gerekmez:

```sh
python -I run_local.py --request examples/demo.json
python -I run_console.py
```

Konsol yalnız `127.0.0.1:8065` üzerinde açılır; tarayıcıda bu yerel adresi ziyaret edin. Örneği çalıştırın, üretilen kodu ve sonucu inceleyin, sonra son kaydı yeniden oynatın. HTTP/model/replay akışları test edildi; bu ortamın tarayıcı ağ politikası nedeniyle canlı Chromium akışı ayrıca doğrulanamadı. CLI örneğinin sonucu -4'tür. Konsol varsayılan olarak journal talebine izin vermez. Yalnız bir süreç-içi journal simülasyonu için `--enable-local-journal` host seçeneği kullanılabilir; hiçbir harici araç bağlanmaz. Kaydedilen yerel dosyalar `local_runs/` altında oluşur.

Negatif örnekler `examples/missing_witness.json`, `wrong_observer.json`, `missing_memory.json`, `denied_journal.json` dosyalarındadır. Serbest metin değil, `initial`, `memory`, `steps` alanlarını taşıyan doğrulanan JSON planı kabul edilir. Kapsam: 16 niyet, 22 işlem/hata sınıfı, 1–32 adım; tamsayı sınırları ve durum kontrolü uygulanır.

## Dil ve eğitim
`source/icl_core/dist/invariant_cognition_language-0.2.1-py3-none-any.whl` bağımsız dil paketidir. `source/icl_native/graph.py` gerçek ICL model grafiğinin host eğitim bağını tanımlar. `models/*/{initial,best,epoch_*,final}` gerçek ağırlık, optimizer ve RNG kayıtlarını içerir. Offline dağıtım seed17'yi kullanır; testte en iyi seed seçilmemiştir.

Test/eğitim ortamında kullanılan sürümler: Python 3.13.5, Torch 2.10.0+cpu, NumPy 2.3.5, safetensors 0.7.0, pytest 9.0.2. Paket bu bağımlılıkları gizlice indirmez veya kurmaz.

```sh
python reproduce.py
python reproduce.py --full-ast-audit
python reproduce.py --retrain-in /yeni/bos/yol/icl_tekrar
```

Varsayılan test çalıştırması yeni geçici kopyada yapılır, teslimdeki ağırlık/veri/manifest bozulmaz. Yeni eğitim yolu mevcutsa işlem reddedilir. Eğitim yalnız eğitim ve doğrulama bölmelerini kullanır; değerlendirme ayrı modüldedir. Başka platformda bit düzeyinde aynı sonuç garantisi yoktur.

## Dosyalar
`SONUC_RAPORU_TR.md`: gerçek sonuçlar ve açık kapsam. `MODEL_CARD.md`: öğrenilen/deterministik katkı ayrımı. `TASK_LEDGER.json`: 18 onaylı görevin durumu. `data/`: yeni veri, bölme ve gerçek AST denetimi. `reports/`: ham tahminler, hatalar, eğitim/değerlendirme ve ayrı süreç logları. `originals/`: korunmuş eski çekirdek ve önceki kaynak belgeleri. `MANIFEST.json`: dosya bütünlüğü.

## Drive
Bu dosyanın mevcut olması Drive'a yükleme kanıtı değildir. Bu turda doğrudan Drive yazma eylemi bulunmadığından uzak yükleme yapılmadı. Verilen Colab aktarım defteri yalnız kullanıcı Google OAuth onayıyla çalışır; gerçek R5 payload ve hashler yoksa durur. Bütün içerik ZIP'te taşınır; dil/model/veri alt paketleri kanonik özel klasörlere kaydedilir. Kamuya paylaşım veya önceki dosyaların üzerine yazma yoktur. Uzak teslim ancak Google'dan geri indirilen byte'lar eşleşip `ICL_R5_DRIVE_READBACK.json` oluşunca tamamdır.

Başlangıç (`initial`) ağırlık anlık görüntüsü optimizer güncellemesi öncesindedir; Adam momentleri henüz oluşmamıştır. Tam optimizer/RNG devamı için `best`, `epoch_*` veya `final` eğitilmiş checkpointlerini kullanın.
