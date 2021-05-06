#!/bin/bash

docker build -t api-collector .
docker tag api-collector 172.18.255.1:5000/api-collector
docker push 172.18.255.1:5000/api-collector

kubectl -n prometheus delete -f api-collector.yaml
kubectl -n prometheus apply -f api-collector.yaml