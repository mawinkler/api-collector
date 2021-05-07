# api-collector

- [api-collector](#api-collector)
  - [About](#about)
    - [Collector Template](#collector-template)
  - [Quick Start](#quick-start)
  - [Example Queries](#example-queries)
    - [Prometheus](#prometheus)
    - [Grafana](#grafana)
  - [Tricks](#tricks)

## About

Generic API-Collector implemented as a Custom Collector for Prometheus. It supports pluggable collectors at runtime!

Two simple collector examples for Workload Security are provided.

### Collector Template

Below, a sample collector template is shown. They must all be located inside the `collectors` directory.

The general structure is as following:

```py
import ...

def collect() -> dict:

    url=open('/etc/mysecrets/url', 'r').read()
    secret=open('/etc/mysecrets/secret', 'r').read()

    # Define your metrics here
    result = {
        "CounterMetricFamilyName": "myname",
        "CounterMetricFamilyHelpText": "myhelp",
        "CounterMetricFamilyLabels": ['attribute1', 'attribute2'],
        "Metrics": []
    }

    url = "https://" + url
    data = {}
    post_header = {
        "Content-type": "application/json",
        "api-secret-key": secret,
        "api-version": "v1",
    }
    response = requests.get(
        url, data=json.dumps(data), headers=post_header, verify=True
    ).json()

    # Error handling

    # Calculate your metrics
    if len(response[]) > 0:
        for item in response[]:
            # Do some calculations

            # Add a single metric
            result['Metrics'].append({
                "attribute1": attribute1,
                "attribute2": attribute2,
                "metric": mymetric
            })

    # Return results
    return result
```

## Quick Start

> This quick start uses Workload Security as an example.

1. Create a config.json

    ```sh
    cp config.json.sample config.json
    ```

    and adapt it to your environment

2. Configure the overrides for your Prometheus deployment to query the api-collector

    ```yaml
    prometheus:
      prometheusSpec:
        additionalScrapeConfigs:
        - job_name: api-collector
          scrape_interval: 30s
          metrics_path: /
          static_configs:
          - targets: ['api-collector:8000']
    ```

    Below, an example for a full deployment is shown. For simplicity, and if you're using the [c1-playground](https://github.com/mawinkler/c1-playground), you can modify the `deploy_prometheus` method to include the `prometheusSpec` and re-run the script `deploy-prometheus-grafana.sh`. Otherwise run the following to deploy Prometheus and Grafana on your cluster.

    ```sh
    kubectl create namespace prometheus --dry-run=client -o yaml | kubectl apply -f -

    cat <<EOF >overrides/overrides-prometheus.yml
    grafana:
      enabled: true
      adminPassword: operator
      service:
        type: LoadBalancer
    prometheusOperator:
      enabled: true
      service:
        type: LoadBalancer
    prometheus:
      enabled: true
      service:
        type: LoadBalancer
      prometheusSpec:
        additionalScrapeConfigs:
        - job_name: api-collector
          scrape_interval: 10s
          metrics_path: /
          static_configs:
          - targets: ['api-collector:8000']
    EOF

    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add stable https://charts.helm.sh/stable
    helm repo update

    helm upgrade \
      prometheus \
      --values overrides/overrides-prometheus.yml \
      --namespace prometheus \
      --install \
      prometheus-community/kube-prometheus-stack
    ```

3. Run Deploy

    ```sh
    ./deploy.sh
    ```

4. The Workload Security collectors do require a secret to work properly. Create it with

    ```sh
    WS_URL="$(jq -r '.ws_url' config.json)"
    WS_API_KEY="$(jq -r '.ws_api_key' config.json)"

    # create workload security secret
    kubectl -n prometheus create secret generic workload-security \
        --from-literal=ws_url=${WS_URL} \
        --from-literal=api_key=${WS_API_KEY} \
        --dry-run=client -o yaml | kubectl apply -f -

    # create workload security secret volume mount
    kubectl -n prometheus patch deployment api-collector --patch "
    spec:
      template:
        spec:
          containers:
            - name: api-collector
              volumeMounts:
              - name: workload-security-credentials
                mountPath: "/etc/workload-security-credentials"
          volumes:
            - name: workload-security-credentials
              secret:
                secretName: workload-security
    "
    ```

5. Now, inject the sample collectors to the running api-collector

    ```sh
    ./deploy-collectors.sh
    ```

6. You should now be able to query prometheus with `PromQL`.

## Example Queries

### Prometheus

Query the total number of assigned IPS rules

```PromQL
sum by (job) (ws_computers_ips_rules_count_total)
```

Query the percentage of computers with IPS mode set to prevent

```PromQL
sum by (job) (ws_computers_ips_mode_prevent_total) / (count by (job)(ws_computers_ips_mode_prevent_total))
```

### Grafana

Query the percentage of computers with IPS mode set to prevent

```Grafana
sum(ws_computers_ips_mode_prevent_total{job="api-collector"}) / (count(ws_computers_ips_mode_prevent_total{job="api-collector"}))
```

## Tricks

Quick shell in the cluster

```sh
kubectl run -it -n prometheus --image=ubuntu ubuntu --restart=Never --rm -- /bin/bash

# in the new shell, execute e.g.
apt update && apt install -y curl
curl http://api-collector:8000
```

Jump into the api-collector

```sh
kubectl exec -it -n prometheus $(kubectl -n prometheus get pods -o json | jq -r '.items[].metadata | select(.name | startswith("api-collector")) | .name') -- /bin/sh
```

Logs of the api-collector

```sh
kubectl -n prometheus logs $(kubectl -n prometheus get pods -o json | jq -r '.items[].metadata | select(.name | startswith("api-collector")) | .name')
```
