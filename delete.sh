#!/bin/bash

set -e

# deploy the api-collector
kubectl -n prometheus delete -f api-collector-patched.yaml || echo -n

for collector in collectors-enabled/*.py; do
    name_configmap=$(basename -s '.py' ${collector//_/-})
    name_collector=$(basename ${collector})

    echo Creating collector ${name_collector} as ${name_configmap}
    kubectl -n prometheus delete configmap ${name_configmap} || echo -n
done
