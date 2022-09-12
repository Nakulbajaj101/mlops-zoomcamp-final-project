#!/bin/bash

cd "$(dirname "$0")"

ENV=$1

# run terraform for ${ENV}
echo "Initialing terraform"
terraform init -backend-config="key=mlops-zoomcamp-project-${ENV}.tfstate" --reconfigure

echo "Running terraform apply"
terraform apply -auto-approve -var-file="vars/${ENV}.tfvars"
