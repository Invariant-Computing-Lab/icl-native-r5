# OCIL / Invariant OS — R5 gerçek çalışma teslimi
13 Ekim 2026 · Çekirdek 0.2.1 · Yeni koşu; R4 checkpoint devamı değil

## Sonuç
Bu paket kaynak kodu, gerçek eğitilmiş ağırlıklar, yerel çıkarım/konsol, veriler ve çalıştırılmış testleri içerir. Önceki 1.630 baytlık kapanış ZIP'inin R4 payload içermediği kendi makbuzuyla saptandı. O dosya model teslimi sayılmaz. R5, kurtarılmış 0.1.0 çekirdeğin üzerine ayrı sürümde geliştirilip rastgele başlangıçtan eğitildi. Eski bildirilen %79,69/%99,38/%29,83 değerleri bu yeni koşunun başlangıç veya yeniden üretilmiş sonuçları değildir.

## Gerçekleştirilen geliştirmeler
Record türleri fonksiyon/modül sınırlarından geçiyor; yerel tip takma adları ve bağlamdan tip alan boş listeler eklendi. Orijinal çekirdek ve arşiv ayrı korundu. ICL model grafiği tipli OCIR üzerinden eğitim backend'ine bağlı; gradient akışı gerçek. Dağıtımda aynı ağırlıklar Python standart kütüphanesi ve ICL VM ile açılıyor; PyTorch / NumPy gerekmiyor. Yerel konsol model önerisini gösterip ICL kodunu çalıştırıyor, kayıt ve checkpoint'i süreç kapandıktan sonra yeniden açabiliyor.

## Çalıştırılmış kontroller
- Çekirdeğin 1.181 kabul kaydı geçti: 77 elle yazılmış, 1.008 diferansiyel, 39 adversarial, 8 tensor, 30 sözleşme, 19 CLI.
- Yeni test dosyaları 72 pytest vakasında geçti; bunun 31'i dil genişletmeleri.
- Ayrı VM replay: 6 test metodu; temiz venv: 8 ayrı-süreç kontrolü; yerel konsol: 10 HTTP/restart kontrolü geçti.
- 12 gradient koordinatında merkezi fark–autograd en büyük hata 1.714e-11.
- Eğitilmiş ağırlıkların 16 satır × 22 logit karşılaştırmasında temiz sürecin ICL Float64 VM çıktısıyla Torch Float32 çıktısı arasındaki en büyük mutlak fark 2.421e-06; atol ve rtol 1e-5.
- 18 eğitim koşusunun optimizer/RNG devam kontrolünde bir sonraki stokastik güncelleme aynen üretildi.
- 2.304 öngörülen tam aday program ICL VM'de çalıştırılıp kontrol edildi.
- AFC yardımcı hesabının 2.044 sonlu durumu geçti; bu yeni bilimsel deney sayısı değildir.

Bu sayılar birbirinden bağımsız binlerce bilimsel deney olarak toplanmaz. Aynı programlar farklı test/kurulum koşullarında tekrar sınanmıştır.

## Veri ve ayrım
28.000 benzersiz girdi-görev grubu, 30.000 örnek: 20.000 eğitim, 2.000 doğrulama, 2.000 ID, 2.000 uzun bileşim ve 2.000 çift / 4.000 karşı-olgusal örnek. Yapı, sayılar ve Boolean bayraklar ayrı rastgele sayı akışlarıyla üretilmiştir. Bölmeler arasında görev grubu/dünya çakışması 0. Tam görev programları bağlamı çalışma zamanında alan ayrı ICL referanslarıyla yeniden çalıştırıldı; literal-silinmiş girdi AST gruplarında da bölmeler arası çakışma 0.

**Sınır:** Özelleştirilmiş çıktı programlarının, özellikle kısa hata çıktılarının bazıları farklı bölmelerde aynıdır. Girdi AST ayrımı, bütün olası matematiksel program eşdeğerliklerinin ayrıldığı veya her üretilen kaynak çıktısının yeni olduğu demek değildir. `data/reference_ast_audit/SUMMARY.json` bu örtüşmeleri ayrıca listeler. Orijinal M03–M07 hedeflerini sınırsız kaynak üretimi için kapatmıyorum.

## Yeni model sonuçları
Aşağıdaki başarı, yapılandırılmış 16 niyet / 22 işlem-hata alanında **ham semantik işlem öneki eşleşmesidir**. Serbest doğal dil veya modelin kendi yazdığı ham sözdizimi başarısı değildir.

| Varyant | ID | Uzun bileşim | Bağımsız bayrak çiftleri |
|---|---:|---:|---:|
| Native | %100,000 | %100,000 | %100,000 |
| Flat-token baseline | %99,850 | %99,600 | %99,825 |
| Bağlam alanları çıkarıldı | %72,717 | %49,783 | %62,667 |
| Witness alanları çıkarıldı | %91,700 | %86,950 | %86,625 |
| Bellek-varlığı alanı çıkarıldı | %94,700 | %93,950 | %94,000 |
| Ek tutarlılık kaybı çıkarıldı | %100,000 | %100,000 | %100,000 |

Her native seed için bütün Boolean kombinasyonları × 147 sayısal sınır kombinasyonundan oluşan 602.112 ek vakada hata 0. Bu, bütün olası sayısal girdiler için ispat değildir. Uzun testte birleştirme ve kesin durum yürütmesi deterministiktir; modelin uzun-vadeli planlamayı öğrendiği iddia edilmez.

Baseline parametre sayısı yakındır fakat ölçülen eğitim süreleri ±%10 eşleşmiyor. Bu yüzden olumlu küçük farktan araştırma üstünlüğü çıkarılmadı. Ek tutarlılık kaybı çıkarıldığında bu görevde skor değişmedi; o katkının üstünlüğü gösterilmedi.

## Kalan kapsam
Genel metinden program üretme/tamamlama/onarma, öğrenilmiş sayısal durum tahmini ve uzun-vadeli bellek, kapsamlı çok-modlu temsil ve 10 eski model ailesinin tam içerik/ağırlık/hak incelemesi henüz tamam değil. Yerel UI gerçek çalışıyor ama eski G51 console'un kaynak düzeyinde rebase'i veya kamu dağıtımı değildir. TASK_LEDGER, 18 onaylı görevin gerçek durumunu saklıyor; hepsi bitti etiketi yok.

## Tarayıcı kapsamı
Yerel HTTP uçtan uca akışları gerçekten çalıştırıldı. Chromium ile canlı tarayıcı testi ise ortamın yönetici ağ politikası tarafından `ERR_BLOCKED_BY_ADMINISTRATOR` ile engellendi. Bu politika aşılmadı. JavaScript sözdizimi kontrol edildi; kaydedilmiş gerçek CLI sonucunun çevrimdışı görseli oluşturuldu. Bu görsel yeni tarayıcı çıkarımı veya canlı tarayıcı kabul testi değildir.

## Drive
Bu turda Drive'dan okuma yapıldı; mevcut eylem listesinde upload/create işlevi sunulmadı. Google Drive eklentisi kurulu, kullanıcı yetkisi var; bu farkı izin bekliyor diye yanlış sunmuyorum. **Drive'a yeni dosya yüklenmedi ve uzak readback makbuzu yok.** Yerel ZIP gerçek model içeriyor. `delivery/upload_drive.py` ve dışarı verilen Colab defteri, kullanıcı OAuth ile yeni özel klasörlere bütün ZIP'i ve ilgili dil/model/veri paketlerini yükler; eski dosyaları değiştirmez; her yüklemeyi geri indirip SHA-256 karşılaştırır. Yardımcı burada Google yetkilendirmesiyle çalıştırılmış değildir.

## Başlangıç
ZIP'i çıkar. Python 3.11+ ile `python -I run_local.py --request examples/demo.json` sonucu -4'tür. `python -I run_console.py` yerel 8065 portunda konsolu açar. `python reproduce.py` testleri ayrı çalışma kopyasında tekrarlar; eğitim bağımlılıkları önceden kurulu olmalıdır. Detaylar README_TR.md ve MODEL_CARD.md'dedir.
