import os

import boto3


class AwsS3Credentials(object):
    def __init__(self, access_key, secret_key, region_name, bucket_name):
        self._s3 = None

        self._access_key = access_key
        self._secret_key = secret_key
        self._region_name = region_name

        self._bucket_name = bucket_name

    def _get_s3(self):
        if self._s3 is None:
            self._s3 = boto3.resource(
                "s3",
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                region_name=self._region_name,
            )

        return self._s3

    def download_folder(self, prefix):
        bucket = self._get_s3().Bucket(self._bucket_name)

        for file in bucket.objects.filter(Prefix=prefix):
            if not os.path.exists(os.path.dirname(file.key)):
                os.makedirs(os.path.dirname(file.key))

            bucket.download_file(file.key, file.key)

    def upload_fileobj(self, file_content, s3_key):
        bucket = self._get_s3().Bucket(self._bucket_name)
        bucket.upload_fileobj(file_content, s3_key)

    def upload_file(self, file_path, s3_key, acl=None):
        bucket = self._get_s3().Bucket(self._bucket_name)
        bucket.upload_file(file_path, s3_key, ExtraArgs=acl)
