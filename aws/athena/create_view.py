from aws.athena.aws_athena import AwsAthena


CODE_SUCCESS = 0
CODE_FAILURE = 1


def view_table(table, view, where_clause):
    return {
        "table": table,
        "view": view,
        "where_clause": where_clause,
    }


class CreateView(AwsAthena):
    @staticmethod
    def generate_query_str_by_view_table(view_table):
        return f"""
            CREATE OR REPLACE VIEW {view_table["view"]} AS
            SELECT *
            FROM {view_table["table"]}
            WHERE {view_table["where_clause"]}
        """

    def run(self, database, view_table):
        query_str = self.generate_query_str_by_view_table(view_table)

        query_execution_id = self.run_query_str(database, query_str)
        if query_execution_id is None:
            return CODE_FAILURE

        return CODE_SUCCESS
