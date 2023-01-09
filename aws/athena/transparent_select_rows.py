import datetime
import io
import tokenize
from ast import literal_eval

from aws.util.retry import retry_function
from aws.athena.select_rows import SelectRows

# https://docs.aws.amazon.com/athena/latest/ug/data-types.html#type-floating
ATHENA_TYPE = {
    "BOOLEAN": bool,
    "TINYINT": int,
    "SMALLINT": int,
    "INT": int,
    "INTEGER": int,
    "BIGINT": int,
    "DOUBLE": float,
    "FLOAT": float,
    "CHAR": str,
    "VARCHAR": str,
    "DATE": str,
    "TIMESTAMP": str,
    "ARRAY": list,
    "JSON": dict,
    "ROW": str,  # Athena struct 가 ROW 로 오기 때문에 일괄 str 처리
}


class TransparentSelectRows(SelectRows):
    def __init__(self):
        super().__init__()

    def run(self, database, query_str, max_results=1000):
        self._column_names = list()  # [id, user_id, title ...]
        self._column_types = list()  # [BIGINT, BOOLEAN, VARCHAR, TIMESTAMP...]
        self._max_results = max_results

        query_execution_id = self.run_query_str(database, query_str)
        if query_execution_id is None:
            return []

        return self.get_query_result_list(query_execution_id, self._max_results)

    def get_query_result_list(self, query_execution_id, max_results):
        next_token = None

        try:
            for i in range(self.max_next_tokens):
                if next_token is not None:
                    query_result = retry_function(
                        self._get_athena().get_query_results,
                        5,
                        QueryExecutionId=query_execution_id,
                        NextToken=next_token,
                        MaxResults=max_results,
                    )
                else:
                    query_result = retry_function(
                        self._get_athena().get_query_results,
                        5,
                        QueryExecutionId=query_execution_id,
                        MaxResults=max_results,
                    )  # default chunk records count is 1000

                next_token = query_result.get("NextToken", None)
                yield self.parse_query_result(query_result, i)

                if next_token is None:
                    break
        except StopIteration:
            return

    def parse_query_result(self, query_result, i):
        parsed_results = list()

        if i == 0:  # first row is column info
            column_info = query_result["ResultSet"]["Rows"].pop(0)
            for column_name in column_info["Data"]:
                self._column_names.append(column_name["VarCharValue"])
            for column_info in query_result["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]:
                self._column_types.append(column_info["Type"].upper())

        for row in list(query_result["ResultSet"]["Rows"]):
            data = row["Data"]
            try:
                item = self.parse_row_data(data)
                parsed_results.append(item)
            except KeyError:
                print(str(data) + " has wrong values.")
                raise KeyError

        return parsed_results

    def parse_row_data(self, data):
        parsed_data = {}
        for idx, column in enumerate(self._column_names):
            unpacked_value = self._convert(data[idx], self._column_types[idx])
            parsed_data[column] = unpacked_value

        return parsed_data

    def _convert(self, data, data_type="VARCHAR"):
        if "VarCharValue" not in data:
            return None

        if data_type == "BOOLEAN":
            return data.get("VarCharValue", "false").lower() == "true"  # Boolean process

        if data_type == "ARRAY" or data_type == "JSON":
            raw_input = data.get("VarCharValue")
            tokens = tokenize.generate_tokens(io.StringIO(raw_input).readline)
            modified_tokens = (
                (tokenize.STRING, repr(token.string))
                if token.type == tokenize.NAME
                else token[:2]
                for token in tokens
            )
            fixed_input = tokenize.untokenize(modified_tokens)
            return literal_eval(fixed_input)

        if data_type == "TIMESTAMP":
            try:
                datetime_object = datetime.datetime.strptime(data.get("VarCharValue"), "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                datetime_object = None
            return datetime_object

        data_class = ATHENA_TYPE[data_type]
        return data_class(data.get("VarCharValue"))
