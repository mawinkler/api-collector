#!/bin/bash

set -e

NAMESPACE="$(jq -r '.namespace' config.json)"
REGISTRY_EMAIL="$(jq -r '.registry_email' config.json)"

docker build -t api-collector .

kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

if [[ $(kubectl config current-context) =~ gke_.* ]]; then
    echo Running on GKE
    GCP_HOSTNAME="gcr.io"
    GCP_PROJECTID=$(gcloud config list --format 'value(core.project)' 2>/dev/null)
    printf '%s\n' "GCP Project is ${GCP_PROJECTID}"
    GCR_SERVICE_ACCOUNT=service-gcrsvc

    if test -f "${GCR_SERVICE_ACCOUNT}_keyfile.json"; then
        printf '%s\n' "Using existing key file"
    else
        printf '%s\n' "Creating Service Account"
        echo ${GCR_SERVICE_ACCOUNT}_keyfile.json
        gcloud iam service-accounts create ${GCR_SERVICE_ACCOUNT}
        gcloud projects add-iam-policy-binding ${GCP_PROJECTID} --member "serviceAccount:${GCR_SERVICE_ACCOUNT}@${GCP_PROJECTID}.iam.gserviceaccount.com" --role "roles/storage.admin"
        gcloud iam service-accounts keys create ${GCR_SERVICE_ACCOUNT}_keyfile.json --iam-account ${GCR_SERVICE_ACCOUNT}@${GCP_PROJECTID}.iam.gserviceaccount.com
    fi

    REGISTRY_HOSTNAME=${GCP_HOSTNAME}/${GCP_PROJECTID}
    REGISTRY_USERNAME=_json_key
    TARGET_IMAGE=api-collector

    cat ${GCR_SERVICE_ACCOUNT}_keyfile.json | docker login -u _json_key --password-stdin https://${GCP_HOSTNAME}
    docker tag ${TARGET_IMAGE} ${GCP_HOSTNAME}/${GCP_PROJECTID}/${TARGET_IMAGE}
    echo Pushing ${GCP_HOSTNAME}/${GCP_PROJECTID}/${TARGET_IMAGE}
    docker push ${GCP_HOSTNAME}/${GCP_PROJECTID}/${TARGET_IMAGE}

    # create container registry secret
    kubectl -n ${NAMESPACE} create secret docker-registry regcred \
    --docker-server=${REGISTRY_HOSTNAME} \
    --docker-username=${REGISTRY_USERNAME} \
    --docker-password="$(cat service-gcrsvc_keyfile.json)" \
    --docker-email=${REGISTRY_EMAIL} \
    --dry-run=client -o yaml | kubectl apply -f -
else
    REGISTRY_HOSTNAME="$(jq -r '.registry_hostname' config.json)":"$(jq -r '.registry_port' config.json)"
    REGISTRY_USERNAME="$(jq -r '.registry_username' config.json)"
    REGISTRY_PASSWORD="$(jq -r '.registry_password' config.json)"
    
    # login, build and push the api-collector
    echo ${REGISTRY_PASSWORD} | \
        docker login ${REGISTRY_HOSTNAME} --username ${REGISTRY_USERNAME} --password-stdin
    docker tag api-collector ${REGISTRY_HOSTNAME}/api-collector
    docker push ${REGISTRY_HOSTNAME}/api-collector

    # create container registry secret
    kubectl -n ${NAMESPACE} create secret docker-registry regcred \
    --docker-server=${REGISTRY_HOSTNAME} \
    --docker-username=${REGISTRY_USERNAME} \
    --docker-password=${REGISTRY_PASSWORD} \
    --docker-email=${REGISTRY_EMAIL} \
    --dry-run=client -o yaml | kubectl apply -f -
fi

# patch api-collector manifest to point to the registry
eval "cat <<EOF
$(<api-collector.yaml)
EOF
" 2> /dev/null > api-collector-patched.yaml

# deploy the api-collector
kubectl -n ${NAMESPACE} apply -f api-collector-patched.yaml
 