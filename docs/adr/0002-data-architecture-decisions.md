# ADR-0002: Veri mimarisi ve zaman/kimlik politikaları

- Status: Accepted
- Date: 2026-07-27
- Scope: Faz 0 foundation; Ethereum Mainnet ilk adapter'ı

## Context

cryptoAML aynı verinin ham kaynağını, işlenmiş canonical halini, graph
ilişkilerini ve araştırma kanıtını birbirine karıştırmamalıdır. Indexer,
normalizer, graph projection, risk motoru ve API ekipleri farklı zamanlarda
aynı kaydı tekrar işleyebilir. Bu nedenle storage sorumlulukları, zaman
alanları, kimlikler ve replay davranışı baştan sabitlenir.

Bu karar Ethereum Mainnet'ten kontrollü block-range alımını ve fixture tabanlı
testleri kapsar. Multi-chain desteği için chain namespace ve adapter sınırları
korunur; ürün kapsamından çıkarılmaz.

## Decisions

### 1. Storage sorumlulukları

| Katman | Sistem | Sorumluluk | Kaynak gerçekliği |
|---|---|---|---|
| Raw archive | Garage/S3-compatible | Provider'dan gelen ham payload, response metadata, payload hash | Değiştirilemez kaynak kaydı |
| Relational/canonical | PostgreSQL | Chain, block, transaction, movement, address, checkpoint ve operasyon state | Uygulamanın sorgulanabilir canonical görünümü |
| Graph | Neo4j Community, local single-node | Address/contract/asset düğümleri ve transfer/interaction ilişkileri | PostgreSQL'den türetilen projection |
| Analytical | Faz 6'da seçilecek columnar store | Büyük hacimli feature, aggregate, backtest ve warehouse sorguları | Yeniden üretilebilir derived görünüm |
| Audit/evidence | PostgreSQL metadata + Garage snapshot | Assessment, provenance, kullanıcı/servis eylemi ve pinned evidence | Sonradan değişmemesi gereken kayıt |

PostgreSQL canonical kaydın sahibi, Neo4j ve analytical katmanlar derived
projection'dır. Graph veya analytical state silinirse checkpoint'ten itibaren
replay ile yeniden üretilebilir.

### 2. Zaman alanları

- `event_time`: Blockchain olayının zincir üzerindeki zamanı; EVM için block
  timestamp. Pencere hesapları ve davranış feature'ları için ana zamandır.
- `observed_time`: Provider veya indexer'ın veriyi gözlemlediği zaman. Gecikme,
  freshness ve provider karşılaştırması için kullanılır.
- `processing_time`: Bizim pipeline'ın kaydı canonical veya derived state'e
  yazdığı zaman. İşleme gecikmesi, replay ve operasyon metrikleri içindir.

Bu alanlar birbirinin yerine kullanılmaz. Geç gelen veri `event_time` ile
doğru pencereye, `observed_time` ile gecikme hesabına girer.

### 3. Kimlik stratejisi

- Chain kimliği: `eip155:<chain_id>` namespace'i; ilk üretim ağı
  `eip155:1` (Ethereum Mainnet).
- Block kimliği: `(chain_namespace, block_hash)`. Block height tek başına
  kimlik değildir; reorg durumunda aynı height farklı hash taşıyabilir.
- Transaction kimliği: `(chain_namespace, tx_hash)`.
- Movement kimliği: `(chain_namespace, tx_hash, movement_locator)`.
  `movement_locator`, ERC event'lerinde `log_index`; native/internal
  hareketlerde deterministic trace path veya türle ayrıştırılmış locator'dır.
- Address kimliği: `(chain_namespace, normalized_address)`. EVM adresi
  karşılaştırma için lowercase saklanır; checksum biçimi yalnızca sunumda
  üretilebilir.
- Kullanıcıya dönen kimlikler bu composite kimliklerin versioned string
  gösterimidir; ham tx hash hiçbir zaman zincir namespace'i olmadan global
  kabul edilmez.

### 4. Idempotency, checkpoint ve replay

- Her raw payload için içerik hash'i ve provider/source metadata saklanır.
- Block, transaction ve movement upsert işlemleri composite kimliklerle
  idempotent çalışır.
- Checkpoint en az `chain_namespace`, `range_end`, `block_hash`, `parser_version`
  ve `processing_status` taşır.
- Teslim modeli at-least-once'tur; consumer duplicate event'i güvenle tekrar
  işleyebilmelidir.
- Replay belirli bir raw snapshot, parser version ve schema version ile
  çalışır; mevcut canonical state'e doğrudan sessiz overwrite yapmaz.
- Rebuild işlemleri önce staging/versioned projection üretir, reconciliation
  başarılı olduktan sonra aktif görünüm değiştirilir.

### 5. Schema migration ve sözleşme

- Canonical, event ve policy sözleşmelerinin ilk paylaşım formatı JSON Schema'dır.
- Her sözleşmede açık `schema_version` bulunur.
- Geriye uyumlu alan ekleme tercih edilir; alan silme veya anlam değiştirme
  yeni major sürüm gerektirir.
- Migration, schema version ve parser version birlikte kaydedilir.
- Event consumer tanımadığı major sürümü başarıyla işlenmiş gibi işaretlemez;
  quarantine/DLQ ve görünür hata üretir.

### 6. Retention ve veri sınıfları

Retention süreleri ülke, müşteri ve deployment politikasına göre
yapılandırılabilir; bu ADR herhangi bir hukuki süre garantisi vermez.

- `raw`: replay için saklanır; sıcak dönemden sıkıştırılmış/arşiv katmanına
  taşınabilir.
- `canonical`: operasyon ve araştırma için uzun ömürlü ana görünüm.
- `derived`: graph, feature ve aggregate state; kaynaklardan yeniden üretilebilir.
- `audit`: kullanıcı/servis eylemleri, assessment geçmişi ve provenance
  metadata'sı; normal derived retention'dan bağımsız korunur.
- `evidence_snapshot`: vakaya veya alarma pinlenen kanıtın immutable snapshot'ı;
  kaynak veri sonradan değişse bile aynı içerikle yeniden açılmalıdır.

Silme ve arşivleme işlemleri policy version, actor/service identity ve audit
event ile izlenir. Local geliştirmede varsayılan credential ve retention
değerleri production için kullanılamaz.

## Local implementation

Neo4j Community `neo4j:2026.06.0` ile local Compose'a eklenmiştir. Tek node,
named volume, Browser (`localhost:7474`) ve Bolt (`localhost:7687`) erişimi
vardır. Bu kurulum graph projection sözleşmesini çalıştırmak içindir; HA,
cluster, backup ve production security bu ADR tarafından seçilmemiştir.

## Consequences

- Mert raw/canonical pipeline'ı, Abdullah graph projection ve risk state'i,
  Can ise API sözleşmesini birbirinin iç veritabanına doğrudan bağlanmadan
  geliştirebilir.
- Composite kimlikler replay ve multi-chain genişlemesini kolaylaştırır.
- Ayrı raw ve derived katmanları disk ve migration maliyeti getirir; bu maliyet
  provenance ve açıklanabilirlik için bilinçli kabul edilmiştir.
- Neo4j local'e erken eklenmiştir; graph sorumluluğu artık yalnızca doküman
  değildir, ancak production topolojisi sonraki fazların kararıdır.
