import os

from prefect.filesystems import S3


ENV = os.getenv("ENVIRONMENT", default="stage")
BUCKET = "prefect-flows-zoomcamp-project-model"

if ENV == "stage":
    BUCKET = f"{BUCKET}-{ENV}"

def create_storage_block(bucket_name: str="", sub_dir: str="", block_name: str=""):
    block = S3(bucket_path=f"{bucket_name}/{sub_dir}")
    block.save(f"{block_name}", overwrite=True)

if __name__ == "__main__":
    create_storage_block(bucket_name=BUCKET, sub_dir="training-monitoring-flows", block_name="training-and-monitoring")
