# cryptoAML

On-Chain Intelligence & Crypto AML Platform; halka açık blockchain verisini
toplayan, kanonik bir modele dönüştüren, graph ilişkilerini analiz eden ve
sonuçları açıklanabilir risk değerlendirmeleri olarak sunan araştırma
platformudur.

> Platform, otomatik kimlik veya hukuki suçluluk kararı üretmez. On-chain
> kanıt, provenance, confidence ve sürümlenmiş risk politikaları üzerinden
> araştırmacıya karar desteği sağlar.

## Yerel geliştirme

### Gereksinimler

- Docker Desktop ve Docker Compose
- GNU Make
- POSIX uyumlu shell

### İlk kurulum

```sh
make bootstrap
```

Bu komut:

1. `.env.example` dosyasından yerel `.env` oluşturur.
2. Compose yapılandırmasını doğrular.
3. PostgreSQL, Garage ve Redpanda imajlarını indirir.
4. Servisleri başlatıp sağlıklı hale gelmelerini bekler.
5. Servis bazlı health-check çalıştırır.

Sonraki çalıştırmalarda:

```sh
make up
make health
make ps
make down
```

Bütün kök komutları görmek için:

```sh
make help
```

## Yerel bağımlılıklar

| Servis | Amaç | Varsayılan adres |
|---|---|---|
| PostgreSQL | Kanonik ve operasyonel ilişkisel veri | `localhost:5432` |
| Garage | S3-compatible raw archive/object storage | `http://localhost:3900` |
| Redpanda | Kafka-compatible dayanıklı event backbone | `localhost:19092` |

`.env.example` içindeki kimlik bilgileri yalnızca local geliştirme içindir.
Staging veya production ortamında kullanılmamalıdır.

## Repository yapısı

```text
apps/        Kullanıcıya ve dış sistemlere açılan uygulamalar
services/    Veri, graph, risk, alert ve case servisleri
packages/    Paylaşılan schema ve platform paketleri
pipelines/   Backfill, feature, projection ve backtesting işleri
infra/       Compose, Helm, Terraform ve dashboard tanımları
docs/        Mimari, ADR, veri sözlüğü, tehdit modeli ve runbook'lar
tests/       Fixture, contract, integration, performance ve security testleri
```

Her bileşen ilerleyen fazlarda kendi build/lint/test sözleşmesini ekleyecek;
kök `Makefile` bu komutların tek giriş noktasıdır.

## Faydalı komutlar

```sh
make config     # Compose yapılandırmasını doğrula
make build      # Workspace build giriş noktası
make lint       # Yapısal ve shell doğrulamaları
make test       # Foundation smoke testleri
make migrate    # Kayıtlı SQL migration'larını çalıştır
make logs       # Servis loglarını izle
```

Local volume'ları silmek geri döndürülemez olduğundan açık onay ister:

```sh
make clean CONFIRM=1
```

## Lisans

Bu repository MIT lisansıyla yayımlanır. Yerel altyapı bağımlılıklarının kendi
lisans koşulları ayrıca geçerlidir.
