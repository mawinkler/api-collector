#!/bin/bash

set -e

NAMESPACE="$(jq -r '.namespace' config.json)"
WS_URL="$(jq -r '.ws_url' config.json)"
C1_URL="$(jq -r '.c1_url' config.json)"
WS_API_KEY="$(jq -r '.ws_api_key' config.json)"

# create workload security secret
kubectl -n ${NAMESPACE} create secret generic workload-security \
    --from-literal=ws_url=${WS_URL} \
    --from-literal=c1_url=${C1_URL} \
    --from-literal=api_key=${WS_API_KEY} \
    --dry-run=client -o yaml | kubectl apply -f -

# create workload security secret volume mount
kubectl -n ${NAMESPACE} patch deployment api-collector --patch "
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
