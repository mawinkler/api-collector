#!/bin/bash

docker build -t api-collector .
docker tag api-collector 172.18.255.1:5000/api-collector
docker push 172.18.255.1:5000/api-collector

# kubectl -n prometheus delete -f api-collector.yaml

kubectl -n prometheus create secret docker-registry regcred \
    --docker-server=172.18.255.1:5000 \
    --docker-username=admin \
    --docker-password=trendmicro \
    --docker-email=info@mail.com \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl -n prometheus create secret generic workload-security \
    --from-file=ws_url=etc/ws_url \
    --from-file=api_key=etc/ws_api_key \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl -n prometheus apply -f api-collector.yaml