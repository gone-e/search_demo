from time import sleep

from aws.emr.aws_emr import (
    AwsEmr,
    SLEEP_IN_SECONDS,
    CODE_CANNOT_READ_STATE,
    CODE_SUCCESS,
    CODE_FAILURE,
    CODE_REACH_TO_MAX_TIME,
)
from aws.emr.response import Response


class AwsEmrModular(AwsEmr):
    def create_job_flow(self) -> str:
        step_list = self.generate_step_list()
        steps_dict = dict(Steps=step_list,)
        self.update_job_flow(steps_dict)

        print(len(step_list), "steps will be launched.")

        response = self.get_emr().run_job_flow(**self._job_flow)
        if not Response.read_http_status_code(response) == 200:
            raise Exception("JobFlow created failed: %s" % response)

        return Response.read_cluster_id(response)

    def check_cluster_state(self, cluster_id=None):
        cluster_id = cluster_id or self.get_cluster_id_by_name(
            self._name, ["STARTING", "BOOTSTRAPPING", "RUNNING", "WAITING"]
        )

        target_states = ["TERMINATED", "TERMINATING"]
        failed_states = ["TERMINATED_WITH_ERRORS"]
        if self.keep_job_flow_alive_when_no_steps:
            target_states + ["WAITING", "RUNNING"]

        num_steps = int(self.max_time_in_seconds_to_wait / SLEEP_IN_SECONDS)
        for _ in range(num_steps):
            response = self.get_emr().describe_cluster(ClusterId=cluster_id)
            state = Response.read_state(response)
            if state is None:
                return CODE_CANNOT_READ_STATE

            if state in target_states:
                termination_code = Response.read_termination_code(response)
                if termination_code == "ALL_STEPS_COMPLETED":
                    return CODE_SUCCESS
                else:
                    print(Response.read_failure_message(response))
                    return CODE_FAILURE

            if state in failed_states:
                print(Response.read_failure_message(response))
                return CODE_FAILURE

            print(state)
            sleep(SLEEP_IN_SECONDS)

        return CODE_REACH_TO_MAX_TIME

    def get_step_by_name(self, cluster_id, step_name) -> dict:
        response = self.get_emr().list_steps(ClusterId=cluster_id)
        matching_steps = list(
            filter(lambda step: step["Name"] == step_name, response["Steps"])
        )

        if len(matching_steps) >= 1:
            return matching_steps[0]
        else:
            raise Exception(f"No step found with name : {step_name}")

    def check_step_state(self, step_name, cluster_id=None, timeout=60 * 60):
        cluster_id = cluster_id or self.get_cluster_id_by_name(
            self._name, ["STARTING", "BOOTSTRAPPING", "RUNNING", "WAITING"]
        )

        target_states = ["COMPLETED"]
        failed_states = ["CANCEL_PENDING", "CANCELLED", "FAILED", "INTERRUPTED"]
        # ongoing_states = ["PENDING", "RUNNING"]

        num_steps = int(timeout / SLEEP_IN_SECONDS)
        for _ in range(num_steps):
            response = self.get_step_by_name(cluster_id, step_name)
            state = Response.read_state_from_all(response)

            if state is None:
                return CODE_CANNOT_READ_STATE

            if state in target_states:
                return CODE_SUCCESS

            if state in failed_states:
                return CODE_FAILURE

            print(state)
            sleep(SLEEP_IN_SECONDS)

        return CODE_REACH_TO_MAX_TIME
