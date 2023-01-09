import boto3
from botocore.config import Config

from airflow.models import Variable

aws = Variable.get("aws", deserialize_json=True, default_var={})


class AwsCloudTrail(object):
    def __init__(self):
        self._cloudtrail = None

    def _get_cloudtrail(self):
        if self._cloudtrail is None:
            self._cloudtrail = boto3.client(
                "cloudtrail", config=Config(retries={"max_attempts": self.max_attempts})
            )

        return self._cloudtrail

    @property
    def max_attempts(self):
        return 3

    @property
    def wait_in_seconds(self):
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

    def lookup_event(self, start, end):
        next_token = None

        try:
            for i in range(self.max_next_tokens):
                if next_token is not None:
                    response = self._get_cloudtrail().lookup_events(
                        LookupAttributes=[
                            {
                                "AttributeKey": "EventName",
                                "AttributeValue": "StartQueryExecution",
                            },
                        ],
                        StartTime=start,
                        EndTime=end,
                        NextToken=next_token,
                    )
                else:
                    response = self._get_cloudtrail().lookup_events(
                        LookupAttributes=[
                            {
                                "AttributeKey": "EventName",
                                "AttributeValue": "StartQueryExecution",
                            },
                        ],
                        StartTime=start,
                        EndTime=end,
                    )
                # print(response)
                if "NextToken" in response:
                    next_token = response["NextToken"]
                else:
                    break

                yield response["Events"]

                if next_token is None:
                    break
        except StopIteration:
            return
