# ADR-0003: Operasyon gözlemlenebilirliği ve health sözleşmesi

- Status: Accepted
- Date: 2026-07-27
- Scope: Faz 0 / F0-K1-C

## Decision

- Uygulama logları JSON structured formatında stdout'a yazılır.
- Correlation için W3C `traceparent` korunur; yoksa servis yeni trace context
  üretir. `trace_id`, loglarda correlation anahtarı olarak görünür.
- OpenTelemetry SDK/API seam'i ilk aşamada dependency-safe no-op fallback ile
  başlatılır. Collector, Jaeger, Prometheus ve Grafana ikinci operasyon
  aşamasında eklenir.
- Servis health sözleşmesi `/livez`, `/readyz` ve `/startupz` endpoint'lerini
  ayırır. Readiness bağımlılık kontrollerini içerir.
- İlk CI katmanı lint, unit test, secret scan ve dependency scan'dir. Compose
  integration smoke testleri servis kodu oluştukça ikinci katmana eklenir.

## Consequences

- Python servisleri ortak `packages/observability/python` paketini kullanabilir.
- Framework bağımlılığı health sözleşmesinden ayrıdır; FastAPI, Flask veya başka
  bir HTTP framework'ü endpoint'leri aynı response modeline bağlayabilir.
- İlk kurulum hafif kalır; merkezi telemetry görünürlüğü daha sonra Collector
  topolojisiyle büyütülür.
- `readyz` dependency-aware olduğu için servis proses olarak ayakta olsa bile
  gerekli storage/event/graph bağımlılığı yoksa trafik almaya hazır sayılmaz.
