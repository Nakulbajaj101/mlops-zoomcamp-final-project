[![CI_TESTS](https://github.com/Nakulbajaj101/mlops-zoomcamp-final-project/actions/workflows/ci-tests.yml/badge.svg?branch=develop%2Fupdate-testing)](https://github.com/Nakulbajaj101/mlops-zoomcamp-final-project/actions/workflows/ci-tests.yml)

[![CD_DEPLOY](https://github.com/Nakulbajaj101/mlops-zoomcamp-final-project/actions/workflows/cd-deploy.yml/badge.svg?branch=main)](https://github.com/Nakulbajaj101/mlops-zoomcamp-final-project/actions/workflows/cd-deploy.yml)

# Bikeshare Rental Batch Analytical Engine

The purpose of the project is to create a bikeshare rental prediction engine, to help Washington's government understand bikeshare rental patterns and which regions to focus on with spending to improve bikeshare rental infrastructure

## Motivation
The analytical team wants to assist the government by building a rental prediction engine (a batch service application), which will help to score past and future data of bike rentals in Washington. The engine will help the government determine past and new trends, as the ways in which people use the service evolves overtime. The insights will enable the government to provide better infrastrure for the bikepaths in Washington DC. The engine delivers on the promise by learning from rides that happended in the near past, and then make predictions on estimated time for each new ride. The predicted outcome is provided in minutes for the ride. Highly disparate predictions can be used to understand infrastructiure problems in the state and help hone on specific regions requiring attention.

## Data Sources
[Data Company](https://ride.capitalbikeshare.com/) -  The data comes from capital bikeshare company
[Datasets](https://s3.amazonaws.com/capitalbikeshare-data/index.html) - The data is collected and made available for consumption on a monthly basis

## Build With
The section covers tools used to run the project

1. Mlflow for experiment tracking, versioning the model
2. Mfllow for model registry and management
3. Prefect for workflow orchistration of model training pipeline, monitoring pipeline and ride scoring pipeline
4. Prefect for scheduling pipelines
5. Evideltly for monitoring of model, data and feature drifts
6. Terraform for provisioning infrastructure for storing mlflow artifacts, prefect block storage and ec2 infrastructure for model training, monitoring and scoring bike rides
7. Github actions for continuous integration and deployment workflows
8. AWS web services as a cloud provider

## Project Folders

1. .github - Contains logic and files for github actions
2. deploy - Contains logic and files for infrastructure as code
3. model-deployment - Contains logic and files for scoring bike share rental in a batch mode, and unit tests and integration tests associated with scoring logic
4. training-and-monitoring - Contains logic for model training and retraining on a schedule. Also contains logic for monitoring model performance and drifts on a schedule, with added logic to conditionally retrain the model when drift is detected

## How to run training - Step by step guide

- Prerequisites
1. Create an AWS IAM role with permissions to create buckets, ec2
2. Add programmatic access to the role and store access key and secret access key securely
3. Initialise the terraform with the IAM role
4. Have anaconda and python 3.9+
5. Have git for cloning the repo

For provisioning Terraform - please check the link below
[Terraform provisioning](https://github.com/Nakulbajaj101/mlops-zoomcamp/tree/main/06-best-practices)

To run it locally or in EC2 instance steps are the same - But infrastructure must be provisioned
1. Run `make apply_stage_local` from the root directory to provision buckets, IAM and EC2
2. Run `make create_monitoring_stage` from the root directory to create prefect flows, deployment and block storage for training and monitoring
3. (Optional) if want to run things on EC2 instance - Please follow this link
    [Environment setup and ssh](https://www.youtube.com/watch?v=IXSiYkP23zo&list=PL3MmuxUbc_hIUISrluw_A7wDSmfOhErJK&index=3)

4. Run `make setup` for the preliminary setup for local or ec2 environment
5. Run `make start_mlflow_stage` in the root directory to start mlflow server
6. In the separate terminal, ensure your aws profile is activated, but not required if you are on ec2
7. Run `cd training-and-monitoring && pipenv install --dev` and then run `pipenv shell`
8. Download the data and run `python get_data.py`
9. Run `cd prefect_training_monitoring` and then run `python model_training.py`
10. To deploy training and run on a schedule run `bash run_training.sh`


## How to run scoring

1. In the root directory run `make create_scoring_stage`
2. In the root directory start mlflow by running `make start_mlflow_stage`
3. Run `cd model-deployment && pipenv install --dev` and then run `pipenv shell`
4. Run `cd prefect_deployment` and then run `python score.py 2022 05`
5. To deploy and keep running on a schedule on EC2 or locally run `bash run.sh`

## How to run monitoring

1. In the root directory start mlflow by running `make start_mlflow_stage`
2. Run `cd training-and-monitoring && pipenv install --dev` and then run `pipenv shell`
3. Run `cd prefect_training_monitoring` and then run `python monitoring.py`
4. To deploy and run on a schedule run `bash run_monitoring.sh`


## How to run tests

1. Run `cd model-deployment`
2. To run unit tests run `make quality_checks`
3. To run integration tests run `make integration_tests`

## How to deploy and destroy infrastructure as code

### Terraform Plan

1. For stage: In the root directory of the repo run `make plan_stage`
2. For prod: In the root directory of the repo run `make plan_prod`

### To provision and apply

1. For stage: In the root directory of the repo run `make apply_stage_local`
2. For prod: In the root directory of the repo run `make apply_prod_local`

### To destroy

1. For stage: In the root directory of the repo run `make destroy_stage_local`
2. For prod: In the root directory of the repo run `make destroy_prod_local`

## Contact for questions or support

Nakul Bajaj @Nakulbajaj101
