#!/bin/bash

set -e

NAMESPACE="$(jq -r '.namespace' config.json)"

# create configmaps containing the python scripts
for collector in collectors-enabled/*.py; do
    name_configmap=$(basename -s '.py' ${collector//_/-})
    name_collector=$(basename ${collector})

    echo Creating collector ${name_collector} as ${name_configmap}
    kubectl -n ${NAMESPACE} create configmap ${name_configmap} \
        --from-file=${collector} --dry-run=client -o yaml | kubectl apply -f -
    
    # patch the api-collector deployment and set annotations to make
    # potential changes in the collectors effective
    kubectl -n ${NAMESPACE} patch deployment api-collector --patch "
spec:
  template:
    metadata:
      annotations:
        ${name_configmap}Hash: $(kubectl -n ${NAMESPACE} get configmap ${name_configmap} -oyaml | sha256sum)
    spec:
      containers:
        - name: api-collector
          volumeMounts:
          - name: ${name_configmap}
            mountPath: "/code/${collector//-enabled//}"
            subPath: ${name_collector}
      volumes:
        - name: ${name_configmap}
          configMap:
            name: ${name_configmap}
"
done
