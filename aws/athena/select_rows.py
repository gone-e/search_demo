import itertools

from aws.athena.aws_athena import AwsAthena
from aws.util.retry import retry_function


class SelectRows(AwsAthena):
    def parse_row_data(self, data):
        raise NotImplementedError

    def get_query_result_list(self, query_execution_id):
        query_result_list = list()
        next_token = None

        for _ in range(self.max_next_tokens):
            if next_token is not None:
                query_result = retry_function(self._get_athena().get_query_results, 5, QueryExecutionId=query_execution_id, NextToken=next_token)
                # self._get_athena().get_query_results(QueryExecutionId=query_execution_id, NextToken=next_token)
            else:
                query_result = retry_function(self._get_athena().get_query_results, 5, QueryExecutionId=query_execution_id)
                # query_result = self._get_athena().get_query_results(QueryExecutionId=query_execution_id)

            query_result_list.append(query_result)
            next_token = query_result.get("NextToken", None)

            if next_token is None:
                return query_result_list

        return query_result_list

    def parse_query_result(self, query_result_list):
        rows = list()
        for query_result in query_result_list:
            rows.append(query_result["ResultSet"]["Rows"])

        parsed_results = list()
        for row in list(itertools.chain(*rows))[1:]:
            data = row["Data"]

            try:
                item = self.parse_row_data(data)
                parsed_results.append(item)
            except KeyError:
                print(str(data) + " has wrong values.")

        return parsed_results

    def run(self, database, query_str):
        query_execution_id = self.run_query_str(database, query_str)
        if query_execution_id is None:
            return []

        query_result_list = self.get_query_result_list(query_execution_id)
        parsed_results = self.parse_query_result(query_result_list)

        return parsed_results
