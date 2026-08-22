import boto3

AWS_REGION = "ap-northeast-2"
ECS_CLUSTER_NAME = "fargate-cluster"
TASK_DEFINITION = "real_estate_crawling"
SUBNET_ID = "subnet-0ff952eb6ed7ef300"  # 실제 값 입력
SECURITY_GROUP_ID = "sg-0710391540fef28fc"  # 실제 값 입력

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