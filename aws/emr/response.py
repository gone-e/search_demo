class Response(object):
    @staticmethod
    def read_http_status_code(response):
        try:
            return response["ResponseMetadata"]["HTTPStatusCode"]
        except KeyError:
            return None

    @staticmethod
    def read_cluster_id(response):
        try:
            return response["JobFlowId"]
        except KeyError:
            return None

    @staticmethod
    def read_state(response):
        try:
            return response["Cluster"]["Status"]["State"]
        except KeyError:
            return None

    @staticmethod
    def read_state_from_all(response):
        try:
            return response["Status"]["State"]
        except KeyError:
            return None

    @staticmethod
    def read_termination_code(response):
        try:
            return response["Cluster"]["Status"]["StateChangeReason"]["Code"]
        except KeyError:
            return None

    @staticmethod
    def read_failure_message(response):
        cluster_status = response["Cluster"]["Status"]
        state_change_reason = cluster_status.get("StateChangeReason")
        if state_change_reason:
            return f'for code: {state_change_reason.get("Code", "No code")} with message {state_change_reason.get("Message", "Unknown")}'

        return None
