#!/bin/bash

set -e

NAMESPACE="$(jq -r '.namespace' config.json)"
REGISTRY_HOSTNAME="$(jq -r '.registry_hostname' config.json)"
REGISTRY_PORT="$(jq -r '.registry_port' config.json)"
REGISTRY_USERNAME="$(jq -r '.registry_username' config.json)"
REGISTRY_PASSWORD="$(jq -r '.registry_password' config.json)"
REGISTRY_EMAIL="$(jq -r '.registry_email' config.json)"

# login, build and push the api-collector
echo ${REGISTRY_PASSWORD} | \
    docker login ${REGISTRY_HOSTNAME}:${REGISTRY_PORT} --username ${REGISTRY_USERNAME} --password-stdin
docker build -t api-collector .
docker tag api-collector ${REGISTRY_HOSTNAME}:${REGISTRY_PORT}/api-collector
docker push ${REGISTRY_HOSTNAME}:${REGISTRY_PORT}/api-collector

kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# create container registry secret
kubectl -n ${NAMESPACE} create secret docker-registry regcred \
    --docker-server=${REGISTRY_HOSTNAME}:${REGISTRY_PORT} \
    --docker-username=${REGISTRY_USERNAME} \
    --docker-password=${REGISTRY_PASSWORD} \
    --docker-email=i${REGISTRY_EMAIL} \
    --dry-run=client -o yaml | kubectl apply -f -

# patch api-collector manifest to point to the registry
eval "cat <<EOF
$(<api-collector.yaml)
EOF
" 2> /dev/null > api-collector-patched.yaml

# deploy the api-collector
kubectl -n ${NAMESPACE} apply -f api-collector-patched.yaml
