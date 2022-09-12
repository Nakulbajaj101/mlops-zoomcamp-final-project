#!/bin/bash
echo "Creating the workqueue"
export work_queue="bikeshare-training-work-queue"

pipenv run prefect work-queue create $work_queue -t "bikeshare_training" -l 1

echo "Deploying the model training"
pipenv run python model_training_deploy.py $work_queue

echo "Starting the agent for the deployment"
prefect agent start --work-queue $work_queue
