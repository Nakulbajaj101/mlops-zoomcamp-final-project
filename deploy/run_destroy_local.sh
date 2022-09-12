#!/bin/bash

cd "$(dirname "$0")"

ENV=$1

if [[ $ENV == "stage" ]]
    then
    export BIKESHARE_SCORED_DATA_STORAGE="bikeshare-scored-data-${ENV}"
    export PREFECT_ARTIFACTS_SCORING_STORAGE="prefect-flows-zoomcamp-project-scoring-${ENV}"
    export PREFECT_ARTIFACTS_TRAINING_MONITORING_STORAGE="prefect-flows-zoomcamp-project-model-${ENV}"
    export MLFLOW_BACKEND_STORAGE="bikeshare-model-artifacts-${ENV}"
elif [[ $ENV == "prod" ]]
    then
    export BIKESHARE_SCORED_DATA_STORAGE="bikeshare-scored-data"
    export PREFECT_ARTIFACTS_SCORING_STORAGE="prefect-flows-zoomcamp-project-scoring"
    export PREFECT_ARTIFACTS_TRAINING_MONITORING_STORAGE="prefect-flows-zoomcamp-project-model"
    export MLFLOW_BACKEND_STORAGE="bikeshare-model-artifacts"
else
    echo "Value must be either stage or prod"
    exit 1
fi

aws s3 rm s3://$BIKESHARE_SCORED_DATA_STORAGE --recursive
aws s3 rm s3://$PREFECT_ARTIFACTS_SCORING_STORAGE --recursive
aws s3 rm s3://$PREFECT_ARTIFACTS_TRAINING_MONITORING_STORAGE --recursive
aws s3 rm s3://$MLFLOW_BACKEND_STORAGE --recursive

echo "Initialising terraform"
terraform init -backend-config="key=mlops-zoomcamp-project-${ENV}.tfstate" --reconfigure

echo "Running terraform destroy"
terraform destroy -auto-approve -var-file="vars/${ENV}.tfvars"
