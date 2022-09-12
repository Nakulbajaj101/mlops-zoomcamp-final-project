import sys

from prefect.deployments import Deployment
from prefect.filesystems import S3
from prefect.orion.schemas.schedules import CronSchedule
from score import batch_score

storage = S3.load("scoring")

deployment = Deployment.build_from_flow(
    flow=batch_score,
    schedule=CronSchedule(cron="0 3 2 * *"),
    work_queue_name=sys.argv[1],
    parameters={"date": None},
    name="bikeshare-score-deployment",
    storage=storage,
    tags=["ml", "bikeshare_prediction"],
)

deployment.apply()
