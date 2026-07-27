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

Görev durumu Project üzerinde, teknik kararlar ADR içinde, kod değişiklikleri
ise branch ve pull request üzerinde takip edilir. Sohbette alınan karar,
ADR/issue'a yazılmadıysa ekip kararı kabul edilmez; sohbet geçmişi arşiv değil,
hafızası da biraz nazlıdır.

## Onaylanan ortak teknik kararlar

Bu kararlar F0-K1-B için temel referanstır:

1. İlk canlı veri kapsamı Ethereum Mainnet'ten kontrollü block-range alımıdır.
   Testler sabit fixture kullanır; ilk aşamada bütün Mainnet'i indirmeyiz.
2. Veri/indexer/analitik servislerinde Python, API ve arayüz tarafında ise
   teknoloji-bağımsız JSON sözleşmeleri kullanılır. Can'ın UI framework'ü bu
   sözleşmeye göre seçilebilir.
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

Detaylı karar kaydı, F0-K1-B branch'inin
[`docs/adr/0002-data-architecture-decisions.md`](https://github.com/mertbektaas/cryptoAML/blob/agent/f0-data-architecture-decisions/docs/adr/0002-data-architecture-decisions.md)
dosyasındadır. Branch PR'ı merge edildiğinde bu bağlantı `main` içindeki dosyaya
taşınacaktır.

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

## Branch, PR ve teslim kuralı

1. Her görev için `agent/f<faz>-<alan>-<kisa-aciklama>` branch'i açılır.
2. Commit tek bir anlaşılır işi anlatır.
3. PR açıklamasında issue numarası, değişen sözleşme, testler ve replay/migration
   etkisi yazılır.
4. İlgili sahip review etmeden PR merge edilmez.
5. Yeni alan eklemek geriye uyumlu değilse schema major version ve migration
   notu gerekir.
6. Bir görev “kod yazıldı” diye değil; test, log/metric, hata davranışı,
   dokümantasyon ve entegrasyon örneği tamamlanınca kapanır.

## Faz 0 için günlük çalışma sırası

1. Mert: local Compose ve veri mimarisi temelini açar.
2. Abdullah: canonical/event/policy JSON Schema ve fixture sözleşmelerini
   yayımlar.
3. Can: OpenAPI, auth sınırı ve mock ekranları bu sözleşmelerden tüketir.
4. Üç kişi birbirinin gerçek veritabanını beklemeden mock/fixture ile çalışır.
5. Faz 0 kapanışında raw → canonical → API/fixture akışı ve yanlış tenant
   erişimi birlikte doğrulanır.
