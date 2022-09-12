variable "bikeshare_scored_data_storage" {
    default = "bikeshare-scored-data"
    description = "bucket where stored predictions live"
}

variable "prefect_artifacts_scoring_storage" {
    default = "prefect-flows-zoomcamp-project-scoring"
    description = "Bucket with prefect block storage for scoring"
}

variable "prefect_artifacts_training_monitoring_storage" {
    default = "prefect-flows-zoomcamp-project-model"
    description = "Bucket with prefect block storage for training and monitoring"
}

variable "mlflow_backend_storage" {
    default = "bikeshare-model-artifacts"
    description = "Bucket for storing mlflow model, runs and experiments metadata and artifacts"
  
}

variable "env" {
    default = "stage"
}

variable "aws_region" {
    default = "us-east-2"
}

variable "bikeshare_training_instance_name" {
    type = string
    default = "bikeshare-rental-training-instance"
}

variable "bikeshare_rental_instance_volume_size" {
    default = 30
}

variable "bikeshare_rental_key_name" {
    type = string
    default = "mlops-zoomcamp-project"
}