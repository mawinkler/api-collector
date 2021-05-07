#!/bin/bash

for collector in collectors/*.py; do
    name_configmap=$(basename -s '.py' ${collector//_/-})
    name_collector=$(basename ${collector})

    echo Creating collector ${name_collector} as ${name_configmap}
    kubectl -n prometheus create configmap ${name_configmap} \
        --from-file=${collector} --dry-run=client -o yaml | kubectl apply -f -
    kubectl -n prometheus patch deployment api-collector --patch "
spec:
  template:
    spec:
      containers:
        - name: api-collector
          volumeMounts:
          - name: ${name_configmap}
            mountPath: "/code/${collector}"
            subPath: ${name_collector}
      volumes:
        - name: ${name_configmap}
          configMap:
            name: ${name_configmap}
"
done

# restart the api-collector
kubectl -n prometheus delete pod $(kubectl -n prometheus get pods -o json | jq -r '.items[].metadata | select(.name | startswith("api-collector")) | .name')
