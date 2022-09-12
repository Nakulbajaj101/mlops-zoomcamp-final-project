from prefect.deployments import Deployment
from prefect.filesystems import S3
from prefect.orion.schemas.schedules import CronSchedule

from monitoring import model_monitoring

storage = S3.load("training-and-monitoring")

deployment = Deployment.build_from_flow(
    flow=model_monitoring,
    schedule=CronSchedule(cron="0 3 3 * *"),
    work_queue_name="bikeshare-work-queue",
    parameters = {
        "date": None, "retraining": False
    },
    name="bikeshare-monitoring-deployment",
    storage=storage,
    tags=["ml","bikeshare_model_monitoring"]
)

deployment.apply()
