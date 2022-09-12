#!/bin/bash
cd "$(dirname "$0")"

export BUCKET_NAME="bike-duration"
export INPUT_FILE_PATTERN="s3://${BUCKET_NAME}/in/{year:04d}-{month:02d}.parquet"
export OUTPUT_FILE_PATTERN="s3://${BUCKET_NAME}/out/{year:04d}-{month:02d}.parquet"
export S3_ENDPOINT_URL="http://localhost:4566/"

# Getting localstack up
docker-compose up -d 
for t in {1..10};
    do echo checking service up 
    healthy=$(docker inspect -f '{{ .State.Health.Status }}' integration-tests_localstack_1)
    echo $healthy
    if [[ $healthy == 'healthy' ]]
    then 
        echo service is up
        break
    fi 
    sleep $t 
    echo sleeping for $t seconds
done

# creating bucket    
aws --endpoint-url ${S3_ENDPOINT_URL} s3 mb s3://${BUCKET_NAME}

# run integration tests
echo "Running tests"
python test_score.py 2022 05

echo "Finishes tests"

RESULT=$?
if [ $RESULT -eq 0 ]; then
  echo Integration tests passed
else
  docker-compose logs
  echo Integration tests failed
fi

docker-compose down
