#!/bin/bash

cd "$(dirname "$0")"

ENV=$1

# run terraform for ${ENV}
echo "Initialising terraform"
terraform init -backend-config="key=mlops-zoomcamp-project-${ENV}.tfstate" --reconfigure

echo "Running terraform plan"
terraform plan -var-file="vars/${ENV}.tfvars"
