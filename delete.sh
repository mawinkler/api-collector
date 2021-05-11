#!/bin/bash

set -e

NAMESPACE="$(jq -r '.namespace' config.json)"

# deploy the api-collector
kubectl -n ${NAMESPACE} delete -f api-collector-patched.yaml || echo -n

for collector in collectors-enabled/*.py; do
    name_configmap=$(basename -s '.py' ${collector//_/-})
    name_collector=$(basename ${collector})

    echo Deleting collector ${name_collector}
    kubectl -n ${NAMESPACE} delete configmap ${name_configmap} || echo -n
done
