#!/bin/bash

set -e

NAMESPACE="$(jq -r '.namespace' config.json)"
C1_URL=`cat /etc/cloudone-credentials/c1_url`
API_KEY=`cat /etc/cloudone-credentials/api_key`
WS_KEY=`cat /etc/cloudone-credentials/ws_key`

# create workload security secret
kubectl -n ${NAMESPACE} create secret generic cloudone \
    --from-literal=c1_url=${C1_URL} \
    --from-literal=api_key=${API_KEY} \
    --from-literal=ws_key=${WS_KEY} \
    --dry-run=client -o yaml | kubectl apply -f -

# create workload security secret volume mount
kubectl -n ${NAMESPACE} patch deployment api-collector --patch "
spec:
  template:
    spec:
      containers:
        - name: api-collector
          volumeMounts:
          - name: cloudone-credentials
            mountPath: "/etc/cloudone-credentials"
      volumes:
        - name: cloudone-credentials
          secret:
            secretName: cloudone
"
