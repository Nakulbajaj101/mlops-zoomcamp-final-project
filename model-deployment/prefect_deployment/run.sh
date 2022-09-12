#!/bin/bash
echo "Creating the workqueue"
export work_queue="bikeshare-scoring-work-queue"

pipenv run prefect work-queue create $work_queue -t "bikeshare_prediction" -l 1

echo "Deploying the batch scoring"
pipenv run python score_deploy.py $work_queue

echo "Starting the agent for the deployment"
prefect agent start --work-queue $work_queue
