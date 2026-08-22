import boto3
import io
import json
from datetime import datetime
import os


def _s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION', 'ap-northeast-2')
    )


def load_seen_cases(bucket_name, key="court_data/seen_cases.json"):
    """
    이전 실행에서 이미 처리한 사건번호 집합을 S3에서 불러온다.
    매주 스케줄 실행 시 같은 매물을 반복 처리하지 않기 위한 상태 저장소
    (2026-08-22 추가). 파일이 없으면(최초 실행) 빈 set을 반환한다.
    """
    try:
        obj = _s3_client().get_object(Bucket=bucket_name, Key=key)
        return set(json.loads(obj['Body'].read().decode('utf-8')))
    except Exception as e:
        print(f"이전 처리 이력 없음 또는 로드 실패 (최초 실행으로 간주): {e}")
        return set()


def save_seen_cases(case_numbers, bucket_name, key="court_data/seen_cases.json"):
    """
    이번 실행에서 처리한 사건번호 집합을 기존 이력과 합쳐 S3에 저장한다.
    """
    try:
        existing = load_seen_cases(bucket_name, key)
        merged = sorted(existing | set(case_numbers))
        _s3_client().put_object(
            Bucket=bucket_name, Key=key,
            Body=json.dumps(merged, ensure_ascii=False).encode('utf-8')
        )
        print(f"처리 이력 저장: s3://{bucket_name}/{key} (누적 {len(merged)}건)")
        return True
    except Exception as e:
        print(f"처리 이력 저장 실패: {e}")
        return False



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