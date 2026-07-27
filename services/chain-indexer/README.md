# Chain indexer

F1-K1-A'nın ilk Go vertical slice'ı Ethereum JSON-RPC provider'larından block
ve transaction receipt verisini alır, provider/source metadata ve SHA-256 hash
ile ortak raw envelope üretir ve gzip'li olarak archive writer'a verir.

## Sınır

Bu servis canonical Chain/Transaction/Movement kayıtları üretmez. Raw envelope
üzerinden canonical dönüşüm F1-K2-A normalizer görevidir. Böylece provider
formatı ile risk/API servisleri birbirine yapışmaz.

## Akış

- `provider.RPCClient`: standart Ethereum JSON-RPC HTTP çağrısı.
- `provider.Resilient`: birincil/yedek provider, retry, exponential backoff ve
  jitter.
- `provider.CircuitBreaker`: sürekli başarısız provider grubuna geçici fren.
- `indexer.Indexer.RunRange`: kontrollü geçmiş block aralığı.
- `indexer.Indexer.RunLive`: yeni block polling/live-tail.
- `archive.S3Writer`: Garage dahil S3-compatible object storage.
- `archive.FileWriter`: CI ve fixture testleri için yerel writer.

Çalıştırılabilir CLI ve checkpoint/pending-confirmed-finalized persistence,
F1-K1-B kapsamındadır; bu paket şu an adapter sınırını ve test edilebilir veri
akışını kurar.
