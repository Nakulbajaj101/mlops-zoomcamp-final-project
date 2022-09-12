import os
import zipfile

import requests
from mlflow.tracking import MlflowClient
from tqdm import tqdm


def download_data(destination_dir: str="", filename: str=""):
    """Function to get data from the s3"""

    # Change the url based on what works for you whether s3 or cloudfront
    url = f"https://s3.amazonaws.com/capitalbikeshare-data/{filename}"
    resp = requests.get(url, stream=False)
    save_path = f"{destination_dir}/{filename}"
    with open(save_path, "wb") as handle:
        for data in tqdm(resp.iter_content(),
                            desc=f"{filename}",
                            postfix=f"save to {save_path}",
                            total=int(resp.headers["Content-Length"])):
            handle.write(data)

    # Extract zip files
    with zipfile.ZipFile(save_path, 'r') as zip_ref:
        zip_ref.extractall(destination_dir)

    # Remove zip files
    os.remove(save_path)


def get_run_id(tracking_uri: str="", model_name: str="", stage: str="Production"):
    """Get model run id"""

    client = MlflowClient(tracking_uri=tracking_uri)
    model_metadata = client.get_latest_versions(name=model_name, stages=[stage])[0]
    run_id = model_metadata.run_id

    return run_id
