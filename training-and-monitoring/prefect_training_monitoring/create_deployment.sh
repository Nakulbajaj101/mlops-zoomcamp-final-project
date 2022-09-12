#!/bin/bash
cd "$(dirname "$0")"

echo "Installing dependencies"
cd .. && pipenv install --dev
cd prefect_training_monitoring

echo "Creating block storage"
pipenv run python prefect_storage.py

echo "Creating training deployment"
pipenv run prefect deployment build ./model_training.py:model_training --name "Model Training Deployment-${ENVIRONMENT}" --storage-block s3/training-and-monitoring

echo "Creating monitoring deployment"
pipenv run prefect deployment build ./monitoring.py:model_monitoring --name "Model Monitoring Deployment-${ENVIRONMENT}" --storage-block s3/training-and-monitoring 