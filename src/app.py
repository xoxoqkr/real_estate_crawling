import time

"""
aws --version
aws configure
aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin 730335187691.dkr.ecr.eu-north-1.amazonaws.com
aws ecr create-repository --repository-name my-python-app
docker build -t my-python-app .
docker tag my-python-app:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/my-python-app:latest
docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/my-python-app:latest

"""



while True:
    print("Running Python script on AWS Fargate...")
    time.sleep(60)  # Sleep for 60 seconds