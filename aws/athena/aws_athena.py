from time import sleep

import boto3
from botocore.config import Config

from airflow.models import Variable

aws = Variable.get(
    "aws",
    deserialize_json=True,
    default_var={
        "s3_path": {
            "application": "bucketplace-emr/data-batch/data-batch-assembly-0.1.0-SNAPSHOT.jar",
            "application-stage": "bucketplace-emr/data-batch-stage/data-batch-assembly-0.1.0-SNAPSHOT.jar",
            "log_uri": "bucketplace-emr/logs/",
            "appsflyer": "bucketplace-appsflyer",
            # "athena-result": "bucketplace-athena-result/",
            # TODO: 개인 로컬 실험용도로 경로를 변경한다. 권한 문제 때문인듯
            "athena-result": "bucketplace-athena-result/",
            "ohs_logs": "bucketplace-hive/log/ohs_logs",
            "ohs_logs2": "bucketplace-hive/log/ohs_logs2",
            "stage_ohs_logs": "bucketplace-hive/log/stage_ohs_logs",
            "access_log": "ohouse-web-prod-access-log/AWSLogs/387471694114/elasticloadbalancing/ap-northeast-2",
        }
    },
)


class AwsAthena(object):
    def __init__(self):
        self._athena = None

    def _get_athena(self):
        if self._athena is None:
            self._athena = boto3.client(
                "athena", config=Config(retries={"max_attempts": self.max_attempts})
            )

        return self._athena

    @property
    def max_attempts(self):
        return 0

    @property
    def result_configuration(self):
        return {
            "OutputLocation": f"s3://{aws.get('s3_path')['athena-result']}",
        }

    @property
    def wait_in_seconds(self):
        return 60

    @property
    def max_sleep_in_seconds(self):
        return 60

    @property
    def max_next_tokens(self):
        return 100000

    @staticmethod
    def get_state(query_execution):
        try:
            return query_execution["QueryExecution"]["Status"]["State"]
        except KeyError:
            return None

    def run_query_str(self, database, query_str):
        query_start = self._get_athena().start_query_execution(
            QueryString=query_str,
            ResultConfiguration=self.result_configuration,
            QueryExecutionContext={"Database": database},
        )

        sleep_in_seconds = 1

        for _ in range(self.wait_in_seconds):
            query_execution = self._get_athena().get_query_execution(
                QueryExecutionId=query_start["QueryExecutionId"]
            )
            state = self.get_state(query_execution)

            if state is None:
                raise Exception(f"Cannot identify {query_str} on {database} state.")

            elif state == "FAILED":
                raise Exception(f"{query_str} on {database} is failed.")

            elif state == "CANCELLED":
                raise Exception(f"{query_str} on {database} is cancelled.")

            elif state == "SUCCEEDED":
                print(f"{query_str} on {database} is successful.")
                return query_start["QueryExecutionId"]

            else:
                print(state)
                sleep(sleep_in_seconds)
                sleep_in_seconds = min(
                    sleep_in_seconds * 2, self.max_sleep_in_seconds
                )  # exponentially back-off

        raise Exception(f"{query_str} exceeded runtime wait limit")

    # return EngineExecutionTimeInMillis, DataScannedInBytes
    def get_amount_scanned(self, query_execution_id):
        query_execution = self._get_athena().get_query_execution(
            QueryExecutionId=query_execution_id
        )
        stats = query_execution["QueryExecution"]["Statistics"]

        return stats["EngineExecutionTimeInMillis"], stats["DataScannedInBytes"]
