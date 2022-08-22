import boto3

from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DATE, S3_BUCKET
from logger import stdout_log


class S3Conn:
    def __init__(self):
        self.s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    def upload_file(self, file: str, per_city: bool = True):
        year, month, day = DATE.split('-')
        full_path: str = f'fb/year={year}/month={month}/day={day}/per-city/{file}' if per_city else f'fb/year={year}/month={month}/day={day}/{file}'

        self.s3.upload_file(file, S3_BUCKET, full_path)
        stdout_log.info(f"File {full_path} uploaded on s3.")

    def download_file(self, full_path: str, file_name: str):
        self.s3.download_file('cic-crawler-dev', full_path, file_name)


s3_conn = S3Conn()
