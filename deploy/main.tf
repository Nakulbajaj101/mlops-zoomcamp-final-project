terraform {
  backend "s3" {
    bucket = "tf-state-mlops-zoomcamp-nbajaj"
    key = "mlops-zoomcamp-project-stage.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
    region = var.aws_region
}

resource "aws_iam_role" "bikeshare_rental_role" {
    name = var.env == "prod" ? "bikesharerental-role" : "bikesharerental-role-${var.env}"
    assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_instance_profile" "bikeshare_rental_profile" {
    name = var.env == "prod" ? "bikeshare-rental-profile" : "bikeshare_rental_profile-${var.env}"
    role = aws_iam_role.bikeshare_rental_role.name
}

resource "aws_iam_role_policy" "bikeshare_rental_role_policy" {
  name = var.env == "prod" ? "bikerental-role-policy" : "bikerental-role-policy-${var.env}"
  role = "${aws_iam_role.bikeshare_rental_role.id}"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["${module.scored_bikeshare_data_storage.bucket_arn}",
                   "${module.prefect_backend_scoring_storage.bucket_arn}",
                   "${module.mlflow_backend_storage.bucket_arn}",
                   "${module.prefect_backend_storage_training_and_monitoring.bucket_arn}"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": ["${module.scored_bikeshare_data_storage.bucket_arn}/*",
                   "${module.prefect_backend_scoring_storage.bucket_arn}/*",
                   "${module.mlflow_backend_storage.bucket_arn}/*",
                   "${module.prefect_backend_storage_training_and_monitoring.bucket_arn}/*"]
    }
  ]
}
EOF
depends_on = [
  module.scored_bikeshare_data_storage.bucket_name,
  module.prefect_backend_scoring_storage.bucket_name,
  module.mlflow_backend_storage.bucket_name,
  module.prefect_backend_storage_training_and_monitoring.bucket_name
]
}

module "scored_bikeshare_data_storage" {
  source = "./modules/storage"
  bucket = var.env == "prod" ? var.bikeshare_scored_data_storage : "${var.bikeshare_scored_data_storage}-${var.env}"
  tags = var.env
}

module "prefect_backend_scoring_storage" {
  source = "./modules/storage"
  bucket = var.env == "prod" ? var.prefect_artifacts_scoring_storage : "${var.prefect_artifacts_scoring_storage}-${var.env}"
  tags = var.env
}

module "mlflow_backend_storage" {
    source = "./modules/storage"
    bucket = var.env == "prod" ? var.mlflow_backend_storage : "${var.mlflow_backend_storage}-${var.env}"
    tags = var.env
}

module "prefect_backend_storage_training_and_monitoring" {
  source = "./modules/storage"
  bucket = var.env == "prod" ? var.prefect_artifacts_training_monitoring_storage : "${var.prefect_artifacts_training_monitoring_storage}-${var.env}"
  tags = var.env
}

module "bikerental_training_and_deployment_ec2" {
  source = "./modules/ec2"
  instance_name = var.env == "prod" ? var.bikeshare_training_instance_name : "${var.bikeshare_training_instance_name}-${var.env}"
  volume_size = var.bikeshare_rental_instance_volume_size
  instance_profile_id = aws_iam_instance_profile.bikeshare_rental_profile.id
  key_name = var.bikeshare_rental_key_name
  depends_on = [
    aws_iam_role_policy.bikeshare_rental_role_policy
  ]
}
