import boto3
import io
from datetime import datetime
import os



def save_to_s3(df, bucket_name, folder_name):
    """
    DataFrame을 AWS S3에 저장하는 함수입니다.

    Args:
        df (pd.DataFrame): 저장할 데이터프레임
        bucket_name (str): S3 버킷 이름
        folder_name (str): S3 버킷 내 저장할 폴더 이름

    Returns:
        bool: 저장 성공 여부
    """
    try:
        # S3 클라이언트 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'ap-northeast-2')
        )
        
        # 현재 시간을 파일명에 포함
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV 파일로 변환
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        # S3에 업로드
        file_name = f"{folder_name}/court_data_{current_time}.csv"
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