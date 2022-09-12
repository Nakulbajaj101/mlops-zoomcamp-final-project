# Creating monitoring env variable stage
create_monitoring_stage: export ENVIRONMENT = stage

# Creating deployment files stage
create_monitoring_stage:
	bash ./training-and-monitoring/prefect_training_monitoring/create_deployment.sh 

# Creating monitoring env variable stage
create_monitoring_prod: export ENVIRONMENT = prod

# Creating deployment files prod
create_monitoring_prod:
	bash ./training-and-monitoring/prefect_training_monitoring/create_deployment.sh 

# Creating deployment scoring stage
create_scoring_stage: export ENVIRONMENT = stage

create_scoring_stage:
	bash ./model-deployment/prefect_deployment/create_deployment.sh

# Creating deployment scoring prod
create_scoring_prod: export ENVIRONMENT = prod

create_scoring_prod:
	bash ./model-deployment/prefect_deployment/create_deployment.sh

# Start mlflow stage
start_mlflow_stage:
	bash ./training-and-monitoring/start_mlflow.sh stage

# Start mlflow prod
start_mlflow_prod:
	bash ./training-and-monitoring/start_mlflow.sh prod

# Plan terraform stage
plan_stage:
	bash ./deploy/run_plan.sh stage

# Plan terraform prod
plan_prod:
	bash ./deploy/run_plan.sh prod

# Apply terraform stage local machine
apply_stage_local:
	bash ./deploy/run_apply_local.sh stage

# Apply terraform prod local machine
apply_prod_local:
	bash ./deploy/run_apply_local.sh prod

# Destroy terraform stage local machine
destroy_stage_local:
	bash ./deploy/run_destroy_local.sh stage

# Destroy terraform prod local machine
destroy_prod_local:
	bash ./deploy/run_destroy_local.sh prod

# For local setup
setup:
	pipenv install --dev 
	pre-commit install