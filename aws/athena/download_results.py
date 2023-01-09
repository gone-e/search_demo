from aws.athena.aws_athena import AwsAthena
from aws.s3.aws_s3 import AwsS3


class DownloadResults(AwsAthena):
    def run(self, database, query_str, filename):
        """
        :param database: The database where the query will execute
        :param query_str: The query string to be executed
        :param filename: The filename of the result csv to be downloaded
        """
        query_execution_id = self.run_query_str(database, query_str)
        if query_execution_id is None:
            raise Exception("Query Failure")

        s3_key = f"athena-result/{query_execution_id}.csv"
        print(f"will download {s3_key} to {filename}")

        downloader = AwsS3("bucketplace-emr")
        downloader.download_file(filename, s3_key)
