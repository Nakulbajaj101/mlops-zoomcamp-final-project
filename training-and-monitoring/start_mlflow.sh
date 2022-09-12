#!/bin/bash
cd "$(dirname "$0")"
if [[ -z "$1" ]]
then 
    ENV="stage"
else 
    ENV=$1
fi

pipenv install --dev

if [[ "$ENV" == "stage" ]]
then 
    pipenv run mlflow server --default-artifact-root s3://bikeshare-model-artifacts-$ENV --backend-store-uri sqlite:///mlflow-$ENV.db 
else
    pipenv run mlflow server --default-artifact-root s3://bikeshare-model-artifacts --backend-store-uri sqlite:///mlflow.db
fi