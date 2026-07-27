# ADR-0001: Local development foundation

- Status: Accepted
- Date: 2026-07-27
- Scope: Local development only

## Context

Faz 0, üç kişinin birbirini beklemeden geliştirme yapabilmesi için ilişkisel
veri, S3-compatible object storage ve Kafka-compatible event backbone ister.
Bu aşamada uygulama dili ve servis deploy sınırları henüz kesinleştirilmemiştir.

## Decision

- PostgreSQL 17.10: kanonik ve operasyonel ilişkisel veri için.
- Garage 2.3.0: local S3-compatible raw archive için.
- Redpanda 26.1.14: local Kafka-compatible event backbone için.
- Docker Compose: tek makinede reproducible local orchestration için.
- Make: build, lint, test, migration ve altyapı komutlarının kök giriş noktası
  için.

## Consequences

- Local ortam tek komutla başlatılıp health-check edilebilir.
- Servisler Kafka/S3/PostgreSQL uyumlu arayüzler üzerinden geliştirilebilir.
- Garage bu fazda tek node ve replication factor 1 ile çalışır; production
  dayanıklılığı sağlamaz.
- Garage AGPL-3.0, Redpanda BSL/Apache bileşenleri ve PostgreSQL kendi lisans
  koşullarına tabidir. Production veya dağıtım kararı öncesinde lisans
  incelemesi ayrıca yapılmalıdır.
- Production topolojisi, secret yönetimi ve HA bu kararla belirlenmez.
