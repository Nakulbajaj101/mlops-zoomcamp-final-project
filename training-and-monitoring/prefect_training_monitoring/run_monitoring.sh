#!/bin/bash
echo "Creating the workqueue"
export work_queue="bikeshare-monitoring-work-queue"

pipenv run prefect work-queue create $work_queue -t "bikeshare_monitoring" -l 1

echo "Deploying the monitoring"
pipenv run python monitoring_deploy.py $work_queue

echo "Starting the agent for the deployment"
prefect agent start --work-queue $work_queue
