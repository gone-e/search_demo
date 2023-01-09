from typing import Optional

import boto3
from botocore.exceptions import ClientError


class AwsS3(object):
    def __init__(self, bucket):
        self._s3 = None
        self._bucket = bucket
        self.total = 0
        self.uploaded = 0

    def _get_s3(self):
        if self._s3 is None:
            self._s3 = boto3.client("s3")

        return self._s3

    def get_obj_size(self, key):
        return self._get_s3().head_object(Bucket=self._bucket, Key=key)['ContentLength']

    def progress(self, size):
        if self.total == 0:
            return
        self.uploaded += size
        progress = int(self.uploaded / self.total * 100)
        if (progress % 20) == 0:
            print("{} %".format(progress))

    def upload_fileobj(self, data, key, total_size=0):
        self.total = total_size
        self.uploaded = 0
        self._get_s3().upload_fileobj(
            Fileobj=data,
            Bucket=self._bucket,
            Key=key,
            Callback=self.progress,
        )

    def list_objects(self, prefix: Optional[str]):
        response = self._get_s3().list_objects_v2(
            Bucket=self._bucket,
            Prefix=prefix,
        )

        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return response["Contents"]

        return None

    def bucket_list_objects(self):
        response = self._get_s3().list_objects_v2(Bucket=self._bucket)

        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return response["Contents"]

        return None

    def copy_object(self, src, dest_bucket, dest_key, acl=None):
        aws_s3_resource = boto3.resource("s3")

        copy_src = {
            "Bucket": self._bucket,
            "Key": src,
        }
        aws_s3_resource.meta.client.copy(copy_src, dest_bucket, dest_key)

        if acl is not None:
            object_acl = aws_s3_resource.ObjectAcl(dest_bucket, dest_key)
            acl_response = object_acl.put(ACL=acl)
            print("acl_response:")
            print(str(acl_response))

            return acl_response["ResponseMetadata"]["HTTPStatusCode"] == 200
        else:
            return True

    def upload_file(self, file, key, acl=None, total_size=0):
        self.total = total_size
        self.uploaded = 0
        self._get_s3().upload_file(
            Filename=file, Bucket=self._bucket, Key=key, Callback=self.progress,
        )

        if acl is not None:
            aws_s3_resource = boto3.resource("s3")
            object_acl = aws_s3_resource.ObjectAcl(self._bucket, key)
            acl_response = object_acl.put(ACL=acl)
            print("acl_response:")
            print(str(acl_response))

            return acl_response["ResponseMetadata"]["HTTPStatusCode"] == 200
        else:
            return True

    def upload_file_acl(self, file, key, acl=None, total_size=0):
        self.total = total_size
        self.uploaded = 0

        try:
            response = self._get_s3().upload_file(Filename=file,
                                                  Bucket=self._bucket,
                                                  Key=key,
                                                  Callback=self.progress,
                                                  ExtraArgs=acl)
            print(str(response))
        except ClientError as e:
            print(e)
            return False
        return True

    def download_file(self, file, key, total_size=0):
        self.total = total_size
        self.uploaded = 0
        self._get_s3().download_file(
            Bucket=self._bucket, Key=key, Filename=file, Callback=self.progress,
        )

    def delete_file(self, key):
        self._get_s3().delete_object(Bucket=self._bucket, Key=key)
