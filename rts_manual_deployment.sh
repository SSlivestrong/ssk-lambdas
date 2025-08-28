set -e
gimme-aws-creds -p default

export COMMIT_HASH=`git log -n 1 --pretty=format:"%H"`
export DCCA_REPO=262403030294.dkr.ecr.us-east-1.amazonaws.com/uat-rts-dcca-service-repo
export TP_REPO=262403030294.dkr.ecr.us-east-1.amazonaws.com/uat-rts-tp-service-repo
export MOCK_HUB_REPO=262403030294.dkr.ecr.us-east-1.amazonaws.com/uat-rts-mock-hub-service-repo
export AWS_PAGER="" # prevents interactive prompt

docker build --progress=plain --tag $DCCA_REPO:$COMMIT_HASH ./regression_test_suite -f  ./regression_test_suite/Dockerfile.dcca-service --no-cache
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $DCCA_REPO
docker push $DCCA_REPO:$COMMIT_HASH
docker tag $DCCA_REPO:$COMMIT_HASH $DCCA_REPO:latest
docker push $DCCA_REPO:latest
aws ecs update-service --cluster uat-rts --service uat-rts-dcca-service --force-new-deployment

docker build --progress=plain --tag $TP_REPO:$COMMIT_HASH ./regression_test_suite -f  ./regression_test_suite/Dockerfile.tp-service --no-cache
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $TP_REPO
docker push $TP_REPO:$COMMIT_HASH
docker tag $TP_REPO:$COMMIT_HASH $TP_REPO:latest
docker push $TP_REPO:latest
aws ecs update-service --cluster uat-rts --service uat-rts-tp-service --force-new-deployment

docker build --progress=plain --tag $MOCK_HUB_REPO:$COMMIT_HASH ./regression_test_suite -f  ./regression_test_suite/Dockerfile.mock-hub-service --no-cache
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $MOCK_HUB_REPO
docker push $MOCK_HUB_REPO:$COMMIT_HASH
docker tag $MOCK_HUB_REPO:$COMMIT_HASH $MOCK_HUB_REPO:latest
docker push $MOCK_HUB_REPO:latest
aws ecs update-service --cluster uat-rts --service uat-rts-mock-hub-service --force-new-deployment