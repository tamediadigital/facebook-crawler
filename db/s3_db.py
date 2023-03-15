import boto3

from utils.logger import stdout_log
from datetime import timedelta, datetime
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DATE, S3_BUCKET, S3_PREFIX


class S3Conn:
    def __init__(self):
        self.s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    def upload_file(self, file: str, per_city: bool = True):
        year, month, day = DATE.split('-')
        full_path: str = f'{S3_PREFIX}/year={year}/month={month}/day={day}/per-city/{file}' if per_city else \
            f'{S3_PREFIX}/year={year}/month={month}/day={day}/{file}'

        self.s3.upload_file(file, S3_BUCKET, full_path)
        stdout_log.info(f"File {full_path} uploaded on s3.")

    def download_file(self, file_name: str, download_in_past=0, per_city=False):
        date = DATE
        if download_in_past:
            _date = datetime.strptime(date, '%Y-%m-%d') - timedelta(days=download_in_past)
            date = _date.strftime("%Y-%m-%d")
        year, month, day = date.split('-')

        full_path: str = f"{S3_PREFIX}/year={year}/month={month}/day={day}/per-city/{file_name}" if per_city else \
            f"{S3_PREFIX}/year={year}/month={month}/day={day}/{file_name}"
        stdout_log.info(f"Downloading: {full_path} from s3.")
        self.s3.download_file(S3_BUCKET, full_path, file_name)

    def delete_file(self, file_name):
        year, month, day = DATE.split('-')
        self.s3.delete_object(Bucket=S3_BUCKET, Key=f"{S3_PREFIX}/year={year}/month={month}/day={day}/{file_name}")
        stdout_log.info(f"File: {file_name} deleted from s3.")
        stdout_log.info(f"{S3_PREFIX}/year={year}/month={month}/day={day}/{file_name}")


s3_conn = S3Conn()
