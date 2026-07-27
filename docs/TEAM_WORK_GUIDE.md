# cryptoAML — Team Work Guide

Bu dosya, Mert, Abdullah ve Can'ın aynı teknik kararları görmesi, görev
sahipliğini bilmesi ve birbirinin ilerlemesini kontrol edebilmesi için ortak
başlangıç noktasıdır.

## Ekip

| Kişi | GitHub | Ana sahiplik |
|---|---|---|
| Mert | [mertbektaas](https://github.com/mertbektaas) | Blockchain veri edinimi, storage, pipeline ve platform altyapısı |
| Abdullah | [acam49](https://github.com/acam49) | Graph, feature, detector, risk, backtest ve intelligence |
| Can | [CanFurkanFidan](https://github.com/CanFurkanFidan) | API, arayüz, kimlik/güvenlik ve araştırmacı ürünü |

Sahiplik, alanın teknik liderliğidir; diğer kişilerin katkı yapmasını
engellemez. Bir değişiklik başka bir alanı etkiliyorsa ilgili kişi review
etmeden görev tamamlanmış sayılmaz.

## Nereden takip edeceğiz?

- GitHub Project: [cryptoAML Project](https://github.com/users/mertbektaas/projects/1)
- Faz 0 parent issue: [#1](https://github.com/mertbektaas/cryptoAML/issues/1)
- F0-K1-A: [#2](https://github.com/mertbektaas/cryptoAML/issues/2)
- F0-K1-B: [#3](https://github.com/mertbektaas/cryptoAML/issues/3)
- F0-K1-C: [#4](https://github.com/mertbektaas/cryptoAML/issues/4)
- F0-K2-A: [#5](https://github.com/mertbektaas/cryptoAML/issues/5)
- F0-K2-B: [#6](https://github.com/mertbektaas/cryptoAML/issues/6)
- F0-K2-C: [#7](https://github.com/mertbektaas/cryptoAML/issues/7)
- F0-K3-A: [#8](https://github.com/mertbektaas/cryptoAML/issues/8)
- F0-K3-B: [#9](https://github.com/mertbektaas/cryptoAML/issues/9)
- F0-K3-C: [#10](https://github.com/mertbektaas/cryptoAML/issues/10)

Görev durumu Project üzerinde, kararların kısa özeti bu dosyada, kod değişiklikleri
ise `main` geçmişinde takip edilir. Bu ekipte kararlar için zorunlu toplantı,
issue tartışması veya pull request bekleme süreci yoktur. Sohbette alınan önemli
bir karar, kaybolmaması için bu dosyaya kısa ve anlaşılır biçimde yazılır.

## Onaylanan ortak teknik kararlar

Bu kararlar F0-K1-B için temel referanstır:

1. İlk canlı veri kapsamı Ethereum Mainnet'ten kontrollü block-range alımıdır.
   Testler sabit fixture kullanır; ilk aşamada bütün Mainnet'i indirmeyiz.
2. Servisler arası iletişim teknoloji-bağımsız JSON/event sözleşmeleriyle
   yapılır. F1-K1 EVM indexer'ının ilk implementasyonu Go olacaktır; risk
   engine gibi sonraki servisler Python kullanabilir. Dil farkı sözleşme,
   version ve contract testleriyle izole edilir.
3. Graph altyapısı local geliştirmede Neo4j Community tek node olarak vardır.
   Browser `http://localhost:7474`, Bolt `bolt://localhost:7687` üzerindedir.
4. Ortak canonical/event/policy sözleşmelerinin ilk formatı JSON Schema'dır.
5. Raw veri katmanlı saklanır; canonical ana görünüm, graph/feature derived
   görünüm, audit/evidence ise ayrı ve izlenebilir kayıttır.
6. Retention süreleri ülke, müşteri ve deployment politikasına göre
   yapılandırılabilir; sabit bir hukuki süre iddiası kod içine gömülmez.
7. Composite kimlikler chain namespace taşır: örneğin Ethereum Mainnet
   `eip155:1`; transaction kimliği chain namespace + tx hash'tir.
8. Teslim modeli at-least-once, consumer davranışı idempotent, replay ise
   parser/schema sürümleriyle tekrarlanabilirdir.

## F0-K2-A Çekirdek Şema Paketleri Kararları (Abdullah - @acam49)

- **Seçilen Mimari Yaklaşım**: **TypeScript + Zod (Monorepo Kütüphanesi & Runtime Validation)**
- **Gerekçe**: Tek kaynaktan tip güvenliği (Type Safety) sağlaması, çalışma anında (runtime) dinamik veri doğrulama yapabilmesi, sıfır derleme karmaşası sunması ve istendiğinde JSON Schema türetebilmesi.
- **Tanımlanan Paketler**:
  1. `@crypto-aml/canonical-schema` (v1.0.0): Address, Transaction, Token, SmartContract, CrossChainBridge varlık şemaları ve doğrulama fonksiyonları.
  2. `@crypto-aml/event-contracts` (v1.0.0): RawIngestedEvent, NormalizedMovementEvent, AssessmentEvent olay sözleşmeleri ve doğrulama fonksiyonları.
  3. `@crypto-aml/policy-schema` (v1.0.0): Signal, Rule, Weight, CapFloor, Tier, Policy risk şemaları ve doğrulama fonksiyonları.
- **Derleme ve Test**: `npm run build` ile `tsc -b` derlemesi, `npm run test` ile Node.js test runner (`node --test`) doğrulaması.

## F0-K2-B Evidence ve Açıklanabilirlik Modeli Kararları (Abdullah - @acam49)

- **Seçilen Mimari Yaklaşım**: **`@crypto-aml/policy-schema` İçine Zod Esaslı Evidence & Metadata Model Katmanı Ekleme**
- **Gerekçe**: Risk değerlendirme sonuçlarının (Assessment) dayandığı somut ham verileri, tetiklenen sinyal gerekçelerini ve tekrarlanabilirlik (provenance) geçmişini tek tip güvenliği altında toplamak.
- **Eklenen Modeller ve Yapılar**:
  1. **EvidenceReferenceSchema**: Ham işlem, event veya yaptırım listesi referansları (`sourceType`, `referenceURI`, `observedAt`).
  2. **QualityMetricsSchema**: `coverage` (% kapsam), `freshnessSeconds` (saniye tazelik), `finality` (kesinlik durumu) ve `confidence` (% güven skoru).
  3. **ExplainedSignalSchema**: Tetiklenen sinyal uyarısı, zorunlu `reason`, `observedValue`, `operator`, `expectedValue`, `contribution` (% risk puanı etkisi) ve `evidenceReferences` dizisi.
  4. **ReproducibilityMetadataSchema**: `datasetSnapshotId`, `featureVersion`, `policyVersion`, `modelVersion`, `codeCommitHash` ve `evaluatedAt` zaman damgası (Past replay / Audit izlenebilirliği).
  5. **AssessmentExplainabilitySchema**: `Evidence → Signal → Assessment` zincirini bağlayan nihai açıklanabilirlik veri yapısı ve `validateAssessmentExplainability` fonksiyonu.

## F0-K2-C Golden Fixture Temeli Kararları (Abdullah - @acam49)

- **Seçilen Mimari Yaklaşım**: **YAML Formatında Fixture ve Graph Topolojisi Tanımları & Deterministik Test Setleri**
- **Gerekçe**: YAML formatının kolay okunabilirliği, yorum satırları taşıyabilmesi, dil bağımsızlığı (Go, Python, TypeScript) ve tüm ekip için ortak referans (Single Source of Truth) oluşturması.
- **Oluşturulan Fixture ve Golden Setler**:
  1. `tests/fixtures/raw-transactions.yaml` (Lisans: MIT): `native_transfer`, `erc20_transfer`, `multiple_events`, `contract_creation` ve `decode_failure` ham veri test örnekleri.
  2. `tests/golden-datasets/normalized-movements.yaml` (Lisans: MIT): Ham verilerin beklenen standart normalize çıktı yanıtları (`native_transfer_golden`, `erc20_transfer_golden`, `contract_creation_golden`, `decode_failure_golden`).
  3. `tests/golden-datasets/graph-topologies.yaml` (Lisans: MIT): `rapid_pass_through` (hızlı transit), `fan_in` (toplama), `fan_out` (dağıtma) ve `label_exposure` (yaptırımlı adres 1-hop/2-hop teması) graph test verileri.
- **Doğrulama ve Otomasyon**: `@crypto-aml/canonical-schema` paketi altına `yaml` bağımlılığı ve `fixtures.test.ts` eklenerek tüm YAML dosyalarının şemalara %100 uyumu test edildi.

## F1-K2-A Kanonik Normalizasyon Kararları (Abdullah - @acam49)

- **Seçilen Mimari Yaklaşım**: **Python Tabanlı Normalizer Servisi (FastAPI / Pydantic & Idempotent Transformation Engine)**
- **Gerekçe**: Ekip sorumluluk haritasındaki Python veri/risk liderliğine tam uyumu, Pydantic v2 ile katı tip güvenliği sunması ve ileride Makine Öğrenmesi/Risk analiz servisleriyle doğrudan yerel entegrasyonu.
- **Mimari ve Servis Bileşenleri (`services/normalizer`)**:
  1. **`models.py`**: `@crypto-aml/canonical-schema` ve `@crypto-aml/event-contracts` ile birebir uyumlu Pydantic modelleri (`AddressModel`, `TransactionModel`, `SmartContractModel`, `NormalizedMovementEventModel`).
  2. **`normalizer.py`**: Ham RPC payload verilerini kanonik yapılara dönüştüren ana motor. Native ETH (wei -> decimal), ERC-20 log parsing (USDT), Akıllı Kontrat Kurulum tespiti (`toAddress: null`), Idempotent mükerrer işleme engeli (`chain:txHash` cache) me mantığı.
  3. **`app.py`**: Proje sağlık sözleşmelerine tam uyumlu `/livez`, `/readyz`, `/startupz` endpoint'leri ve `/normalize` REST servisi.
- **Test ve Otomasyon**: `services/normalizer/tests/test_normalizer.py` altında Native, ERC-20, Contract Creation, Idempotency ve Decode Failure durumlarını kapsayan testler yazıldı ve doğrulandı.

## F1-K2-B Event ve Token Movement Decode Kararları (Abdullah - @acam49)

- **Seçilen Mimari Yaklaşım**: **Python Normalizer İçine `EventDecoder` Modülü ve ABI Registry Katmanı Ekleme**
- **Gerekçe**: EVM log olaylarını (ERC-20, ERC-721, ERC-1155, Uniswap DEX Swaps) harici kütüphane bağımlılığı olmaksızın yüksek performansla ayrıştırarak `NormalizedMovementEventModel` yapılarına çevirmek.
- **Eklenen Modeller ve Decoder Bileşenleri (`services/normalizer/src/decoder.py`)**:
  1. **EVM Topic Hashes**: Standardize `Transfer` (`0xddf252ad...`), `Approval`, `TransferSingle` (ERC-1155), `TransferBatch` ve Uniswap V2/V3 `Swap` topic imzaları.
  2. **ERC-20 & ERC-721 Decoding**: Log topic sayısına göre 3 topic (ERC-20 miktarlı transfer) ve 4 topic (ERC-721 NFT `tokenId` transferi) ayrıştırması.
  3. **ERC-1155 Decoding**: 128 karakterlik veri alanından token ID ve miktar çözümlemesi.
  4. **Uniswap V2 Swap Decoding**: DEX takas olaylarından yönlü varlık aktarımlarını çıkarma.
  5. **Decode Failure Izolasyonu**: Bozuk topic veya eksik data paketlerinde `ValueError` fırlatılarak hatanın servis loglarına kaydedilip izole edilmesi.
- **Test ve Otomasyon**: `services/normalizer/tests/test_decoder.py` altında ERC-20, ERC-721 NFT, Uniswap Swap ve Malformed topic testleri yazıldı ve doğrulandı.





## F1-K1-A EVM adapter kararları

Bu kararlar Mert'in EVM adapter görevinde uygulanır. Performans hedefi yalnızca
programlama dili seçimi değildir; RPC batching, sınırlı paralellik, timeout,
retry/backoff, circuit breaker, raw yazma ve idempotent işleme birlikte ölçülür.

- **Dil:** Go. Adapter, ileride Python kullanabilecek risk engine veya başka
  servislerle JSON/event sözleşmeleri üzerinden konuşur; servislerin aynı dilde
  olması şart değildir.
- **RPC yaklaşımı:** Birincil + yedek provider arayüzü. Provider seçimi
  adapter koduna gömülmez; rate-limit ve geçici hata durumunda fallback yapılır.
- **Çalışma modu:** Kontrollü geçmiş block-range alımı ve live-tail birlikte
  desteklenir. Range-first veya live-tail seçimi ürün kapsamını azaltmaz;
  ikisi aynı adapter sözleşmesinin çalışma modlarıdır.
- **Raw arşiv:** Garage/S3-compatible üzerinde JSON envelope + gzip + SHA-256
  payload hash + provider/source metadata.
- **Hata politikası:** Timeout, exponential backoff ve jitter içeren retry;
  sürekli başarısız provider için circuit breaker.
- **Finality:** Provider'ın `finalized` bilgisini kullan; destek yoksa
  yapılandırılmış confirmation sayısına düşen hibrit politika.
- **Adapter çıktısı:** Ham RPC cevabını koruyan, `chain_namespace`, block
  bilgisi, observed time, provider ve payload hash içeren ortak adapter
  envelope.
- **Canonical geçiş:** Bu görev canonical modele dönüştürme yapmaz. Raw
  envelope'dan canonical Chain/Block/Transaction/Movement kayıtlarını üretme
  işi F1-K2-A normalizer görevidir; adapter yalnızca güvenilir ham veri ve
  ortak envelope yayımlar.

## F0-K1-C operasyon kararları

### Gözlemlenebilirlik yaklaşımı

Bu başlık, sistemin içeride ne yaptığını anlayabilmemizi kapsar:

- Log: bir olayın metinsel/JSON kaydı.
- Metric: olayların sayısal ölçümü; örneğin hata sayısı veya işlem süresi.
- Trace: tek bir isteğin servisler arasındaki yolculuğu.

İlk aşamada JSON structured log kullanılır. Her kayıtta en az timestamp,
level, service, message ve correlation/trace alanları bulunur.

İlk OpenTelemetry adımı yalnızca SDK ve ortak instrumentation iskeletidir;
telemetry console'a veya seçilen basit exporter'a çıkabilir. Daha sonra
OpenTelemetry Collector + Jaeger + Prometheus + Grafana topolojisine geçiş
yapılacaktır. Bu geçiş şimdiden planın parçasıdır; unutulmaması gereken bir
stretch değil, operasyon tabanının sonraki adımıdır.

### Correlation ID ve trace context

İstek dışarıdan `traceparent` ile gelirse W3C Trace Context bilgisi korunur.
Gelmezse ilk servis yeni bir trace/correlation kimliği üretir. Bu kimlik API,
event ve log zinciri boyunca taşınır. Böylece tek bir transaction'ın hangi
servislerden geçtiği aranabilir.

### Health sözleşmesi

Servisler `/livez`, `/readyz` ve `/startupz` endpoint'lerini tanımlar:

- `/livez`: proses ayakta mı?
- `/readyz`: trafik kabul etmeye hazır mı; gerekli dependency'ler erişilebilir mi?
- `/startupz`: ilk açılış/migration tamamlandı mı?

`/readyz` bağımlılık-aware çalışır; PostgreSQL, Redpanda veya Neo4j hazır değilse
servis canlı olsa bile trafik almaya hazır kabul edilmez. Endpoint adlarındaki
`z`, Kubernetes ve cloud-native sistemlerdeki kısa probe adlandırma geleneğidir;
özel bir kriptografi veya gizli ayar değildir.

### CI aşamaları

- İlk aşama: lint + unit test + secret scan + dependency scan.
- Sonraki aşama: bunlara Compose/integration smoke test ve Docker servis
  doğrulaması eklenir.

İkinci aşama bilinçli olarak sonraya bırakılır; servis kodları ve gerçek
integration testleri oluştuğunda CI genişletilir.

Detaylı karar kaydı, F0-K1-B branch'inin
[`docs/adr/0002-data-architecture-decisions.md`](https://github.com/mertbektaas/cryptoAML/blob/agent/f0-data-architecture-decisions/docs/adr/0002-data-architecture-decisions.md)
dosyasındaki gibidir.

## Fazlara göre sahiplik haritası

Her fazdaki üç kişi paralel çalışır; önce ortak sözleşme, sonra mock/fixture,
sonra gerçek entegrasyon yapılır.

| Faz | Mert — veri/platform | Abdullah — graph/risk/intelligence | Can — API/UI/ürün |
|---|---|---|---|
| Faz 0 | F0-K1-A/B/C: repo, storage, veri mimarisi, operasyon ve telemetry | F0-K2-A/B/C: canonical/event/policy şemaları, evidence ve golden fixture | F0-K3-A/B/C: OpenAPI, auth/RBAC/tenant ve web kabuğu |
| Faz 1 | F1-K1-A/B/C: EVM adapter, güvenli indexleme, reconciliation | F1-K2-A/B/C: canonical normalizasyon, token/event decode, doğruluk testleri | F1-K3-A/B/C: address/transaction API, ilk ekranlar, E2E/güvenlik |
| Faz 2 | F2-K1-A/B/C: Neo4j graph projection, bounded query ve feature pipeline | F2-K2-A/B/C: rule policy engine, açıklanabilirlik ve detector'lar | F2-K3-A/B/C: screening API, graph/risk UI ve uçtan uca senaryo |
| Faz 3 | F3-K1-A/B/C: event delivery, snapshot/export storage ve scheduler | F3-K2-A/B/C: alert/case domain servisleri ve doğruluk testleri | F3-K3-A/B/C: alert/case API, araştırmacı ekranları ve audit/E2E |
| Faz 4 | F4-K1-A/B/C: reorg safety, trace/enrichment ve label registry | F4-K2-A/B/C: path/exposure, graph analytics ve backtesting | F4-K3-A/B/C: graph explorer, provenance ve backtest UI/API |
| Faz 5 | F5-K1-A/B/C: contract identity, token pipeline ve davranış feature'ları | F5-K2-A/B/C: pattern kataloğu, contract-risk sinyalleri ve detector governance | F5-K3-A/B/C: contract/token ürünü, görünürlük ve E2E |
| Faz 6 | F6-K1-A/B/C: ek EVM, Bitcoin UTXO, streaming/warehouse/HA | F6-K2-A/B/C: bridge matching, cross-chain tracing ve graph performansı | F6-K3-A/B/C: chain-aware API/UI, monitoring ve release doğrulaması |
| Faz 7 | F7-K1-A/B/C: dataset lineage, model çalıştırma ve serving güvenilirliği | F7-K2-A/B/C: anomaly, supervised/graph intelligence ve model governance | F7-K3-A/B/C: model/policy API, governance dashboard ve E2E |
| Faz 8 | F8-K1-A/B/C: production topology, kurulum modelleri ve operasyon tatbikatları | F8-K2-A/B/C: regression, performans/kaynak güvencesi ve intelligence runbook'ları | F8-K3-A/B/C: security hardening, observability UI ve release kabulü |

Bu tablo görevlerin kısa haritasıdır. Her fazın ayrıntılı kabul ölçütleri,
bağımlılıkları ve alt görevleri proje kapsamındaki faz planında tutulur.

## Kişilerin özellikle bilmesi gereken sınırlar

### Mert — Blockchain veri ve platform mühendisliği

- Raw payload'ı hash ve source metadata'sıyla saklar; normalizer'ın ihtiyaç
  duyduğu veriyi fixture veya event sözleşmesiyle yayımlar.
- PostgreSQL canonical kaydın, Neo4j ve analytical katmanların derived
  projection olduğunu korur.
- Block height'ı tek başına kimlik kabul etmez; block hash ve chain namespace
  kullanır.
- Checkpoint, retry, duplicate ve replay davranışını belgeleyip test eder.
- Risk skorunun anlamını indexer içinde kodlamaz; risk mantığı Abdullah'ın
  policy/detector sözleşmesinden gelir.

### Abdullah — Graph, risk ve analitik mühendisliği

- Graph projection PostgreSQL canonical veriden gelir; indexer tablolarına
  doğrudan bağımlı olmaz.
- Her signal/assessment; policy version, evidence reference, confidence,
  coverage ve freshness taşır.
- Label, cluster veya detector sonucu kesin suçluluk gibi sunulmaz; kaynak ve
  confidence ile birlikte gösterilir.
- Aynı snapshot + aynı policy version replay edildiğinde aynı sonuç üretilir.
- Can'ın API'si için JSON Schema ve OpenAPI örneklerini birlikte günceller.

### Can — API, arayüz ve araştırma ürünü

- UI doğrudan PostgreSQL veya Neo4j'e bağlanmaz; API/OpenAPI sözleşmesini
  kullanır.
- Loading, empty, stale, pending, decode failure, low confidence ve error
  durumlarını gerçek ürün durumu olarak gösterir.
- API'de tenant scope, auth scope, pagination, correlation ID ve standard
  error davranışını korur.
- Kullanıcıyı risk skorundan evidence transaction'ına götüren provenance
  bağlantısını görünür kılar.
- UI teknolojisi değişebilir; canonical/event/assessment sözleşmeleri
  framework'e göre değişmez.

## Hızlı ekip teslim kuralı

Bu üç kişilik staj ekibinde küçük kararlar doğrudan `main` üzerinden ilerler:

1. Önce güncel kodu al: `git pull --rebase origin main`.
2. Kendi görevindeki kodu veya bu rehberdeki kısa kararı güncelle.
3. Tek anlaşılır commit oluştur.
4. `git push origin main` ile doğrudan gönder.
5. Push sonrası Project kartını güncelle; gerekirse ekip sohbetine commit
   bağlantısını bırak.

Sadece şu iki kural sabittir:

- `git push --force` kullanılmaz.
- Aynı dosyada eş zamanlı değişiklik çıkarsa önce ekip arkadaşına haber verilir;
  başkasının değişikliği sessizce ezilmez.

Büyük ve riskli değişikliklerde branch/PR açmak hâlâ kullanılabilir, fakat küçük
görevler için zorunlu değildir. Bir kararın ayrıntılı gerekçesi gerekiyorsa
`docs/adr/` altına kısa bir dosya eklenir; her karar için ADR yazmak şart
değildir.

## Faz 0 için günlük çalışma sırası

1. Mert: local Compose ve veri mimarisi temelini açar.
2. Abdullah: canonical/event/policy JSON Schema ve fixture sözleşmelerini
   yayımlar.
3. Can: OpenAPI, auth sınırı ve mock ekranları bu sözleşmelerden tüketir.
4. Üç kişi birbirinin gerçek veritabanını beklemeden mock/fixture ile çalışır.
5. Faz 0 kapanışında raw → canonical → API/fixture akışı ve yanlış tenant
   erişimi birlikte doğrulanır.
