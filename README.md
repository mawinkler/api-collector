# api-collector

- [api-collector](#api-collector)
  - [Quick Start](#quick-start)
    - [Build Container](#build-container)
    - [Create image pull secret](#create-image-pull-secret)
    - [Run on K8s](#run-on-k8s)
    - [Prometheus Config Snippet:](#prometheus-config-snippet)

Custom Collector for Prometheus

## Quick Start

### Build Container

```sh
docker build -t api-collector .
docker tag api-collector 172.18.255.1:5000/api-collector
docker push 172.18.255.1:5000/api-collector
```

### Create image pull secret

```sh
kubectl -n prometheus create secret docker-registry regcred --docker-server=172.18.255.1:5000 --docker-username=admin --docker-password=trendmicro --docker-email=info@mail.com
```

### Run on K8s

```sh
kubectl -n prometheus apply -f yaml/
```

### Prometheus Config Snippet:

```yaml
prometheus:
  enabled: true
  service:
    type: LoadBalancer
  prometheusSpec:
    additionalScrapeConfigs:
    - job_name: api-collector
      scrape_interval: 10s
      metrics_path: /metrics
      static_configs:
      - targets: ['api-collector:8000']
```
