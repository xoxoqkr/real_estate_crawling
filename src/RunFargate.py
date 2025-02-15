import boto3

AWS_REGION = "eu-north-1"
ECS_CLUSTER_NAME = "fargate-cluster"
TASK_DEFINITION = "real_estate_crawling"
SUBNET_ID = "subnet-0991f2b8b9e37fa3e"  # 실제 값 입력
SECURITY_GROUP_ID = "sg-017bc48d1ea066c2c"  # 실제 값 입력

ecs_client = boto3.client("ecs", region_name=AWS_REGION)

def run_fargate_task():
    response = ecs_client.run_task(
        cluster=ECS_CLUSTER_NAME,
        launchType="FARGATE",
        taskDefinition=TASK_DEFINITION,
        count=1,
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": [SUBNET_ID],
                "securityGroups": [SECURITY_GROUP_ID],
                "assignPublicIp": "ENABLED"
            }
        }
    )
    
    task_arn = response["tasks"][0]["taskArn"]
    print(f"✅ Fargate 작업 실행됨: {task_arn}")

if __name__ == "__main__":
    run_fargate_task()