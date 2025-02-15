import pandas as pd
import numpy as np
import boto3
import io
from datetime import datetime

def create_random_data():
    """
    테스트용 랜덤 데이터를 생성하는 함수
    """
    # 랜덤 데이터 생성
    np.random.seed(42)
    data = {
        'id': range(1, 101),
        'value': np.random.randn(100),
        'category': np.random.choice(['A', 'B', 'C'], 100)
    }
    return pd.DataFrame(data)

def save_to_s3_test():
    """
    테스트용 랜덤 데이터를 생성하여 S3에 저장하는 함수
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        # S3 클라이언트 생성 (with credentials)
        s3_client = boto3.client(
            's3',
            aws_access_key_id='AKIA2UC26SLVUYNLDTU5',      # AWS Access Key ID 입력
            aws_secret_access_key='',     # AWS Secret Access Key 입력
            region_name='eu-north-1'                 # 리전 이름 (예: 서울 리전)
        )
        
        # 테스트 데이터 생성
        df = create_random_data()
        
        # 현재 시간을 파일명에 포함
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV 파일로 변환
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        # S3 버킷과 파일 경로 설정
        bucket_name = "odtest01"  # 실제 S3 버킷 이름으로 변경
        file_name = f"test_data/random_data_{current_time}.csv"
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=csv_buffer.getvalue()
        )
        
        print(f"Successfully saved to S3: s3://{bucket_name}/{file_name}")
        return True
        
    except Exception as e:
        print(f"Error saving to S3: {e}")
        return False

# 테스트 실행
if __name__ == "__main__":
    save_to_s3_test()