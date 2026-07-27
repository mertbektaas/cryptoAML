# Observability package

F0-K1-C'nin Python başlangıç paketidir. Framework bağımsız tutulur; servisler
FastAPI, Flask veya başka bir HTTP katmanı seçebilir.

## İçerik

- `python/cryptoaml_observability/context.py`: W3C `traceparent`, trace/span
  ID ve request-local correlation context.
- `python/cryptoaml_observability/logging.py`: JSON structured log formatter.
- `python/cryptoaml_observability/health.py`: `/livez`, `/readyz` ve
  `/startupz` response modelini besleyen registry.
- `python/cryptoaml_observability/telemetry.py`: OpenTelemetry API seam'i ve
  SDK yokken güvenli no-op fallback.

Local import için:

```sh
PYTHONPATH=packages/observability/python python3 -c \
  'from cryptoaml_observability import TraceContext; print(TraceContext.new())'
```

OpenTelemetry Collector/Jaeger/Prometheus/Grafana bu ilk pakete zorunlu
değildir; operasyon altyapısı olgunlaştığında aynı seam üzerinden eklenir.
