import sys
from aws.s3.aws_s3 import AwsS3
from aws.athena.transparent_select_rows import TransparentSelectRows
from pprint import pprint


if __name__ == "__main__":
    hivedb =  sys.argv[1]
    table = sys.argv[2]

    s3 = AwsS3("bucketplace-emr")
    s3_path = f"hive/output/{hivedb}/{table}"

    loadable_keys = s3.list_objects(s3_path)

    partitions = list()

    athena = TransparentSelectRows()

    for key in loadable_keys:
        partition_str = ','.join([f"{path.split('=')[0]}='{path.split('=')[1]}'" for path in key["Key"].split("/") if "=" in path])
        s3_path_str = '/'.join([f"{path.split('=')[0]}={path.split('=')[1]}" for path in key["Key"].split("/") if "=" in path])

        if partition_str != "" and s3_path_str != "" and "$folder$" not in partition_str:
            partitions.append(f"PARTITION ({partition_str}) location 's3://bucketplace-emr/{s3_path}/{s3_path_str}/'")

    partition_sql = '\n'.join(list(set(partitions)))
    base_sql = f"ALTER TABLE {table} ADD"
    sql = base_sql + '\n' + partition_sql

    athena.run_query_str(hivedb, sql)
