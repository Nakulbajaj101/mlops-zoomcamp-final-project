#!/bin/bash
cd "$(dirname "$0")"

echo "Installing dependencies"
cd .. && pipenv install --dev
cd prefect_deployment

echo "Creating block storage"
pipenv run python prefect_storage.py

echo "Creating scoring deployment"
pipenv run prefect deployment build ./score.py:batch_score --name "Model Scoring Deployment-${ENVIRONMENT}" --storage-block s3/scoring
