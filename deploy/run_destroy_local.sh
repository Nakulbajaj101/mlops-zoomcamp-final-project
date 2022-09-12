#!/bin/bash 

cd "$(dirname "$0")"

ENV=$1

echo "Initialising terraform"
terraform init -backend-config="key=mlops-zoomcamp-project-${ENV}.tfstate" --reconfigure

echo "Running terraform destroy"
terraform destroy -auto-approve -var-file="vars/${ENV}.tfvars"
