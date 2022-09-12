import sys

from prefect.deployments import Deployment
from prefect.filesystems import S3
from prefect.orion.schemas.schedules import CronSchedule

from model_training import model_training

storage = S3.load("training-and-monitoring")

deployment = Deployment.build_from_flow(
    flow=model_training,
    schedule=CronSchedule(cron="0 3 15 */3 *"),
    work_queue_name=sys.argv[1],
    parameters = {
        "date": None, "retraining": False
    },
    name="bikeshare-training-deployment",
    storage=storage,
    tags=["ml","bikeshare_training"]
)

deployment.apply()
