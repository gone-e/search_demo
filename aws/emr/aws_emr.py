from time import sleep
import boto3

from airflow.models import Variable
from setting.env_setting import EnvSetting

from aws.emr.response import Response
from aws.emr.spark_conf import SparkConf

MAX_TIME_WAIT_FOR_STARTING = 20 * 60
SLEEP_IN_SECONDS = 45

CODE_SUCCESS = 0
CODE_CANNOT_READ_CLUSTER_ID = 1
CODE_CANNOT_READ_STATE = 2
CODE_CANNOT_READ_TERMINATION_CODE = 3
CODE_FAILURE = 4
CODE_REACH_TO_MAX_TIME = 5

ec2 = Variable.get(
    "ec2",
    deserialize_json=True,
    default_var={
        "xlarge": {
            "InstanceType": {"name": "r5.xlarge", "v_cpu": 4, "ram": 30},
            "BidPrice": "0.1",
        },
        "2xlarge": {
            "InstanceType": {"name": "r5.2xlarge", "v_cpu": 8, "ram": 62},
            "BidPrice": "0.19",
        },
        "4xlarge": {
            "InstanceType": {"name": "r4.4xlarge", "v_cpu": 16, "ram": 124},
            "BidPrice": "0.35",
        },
        "8xlarge": {
            "InstanceType": {"name": "r4.8xlarge", "v_cpu": 32, "ram": 244},
            "BidPrice": "0.67",
        },
    },
)

aws = Variable.get(
    "aws",
    deserialize_json=True,
    default_var={
        "instances": {
            "Ec2SubnetId": "subnet-04363b72903bf8834",
            "EmrManagedMasterSecurityGroup": "sg-0e1577b7a3ceea170",
            "AdditionalMasterSecurityGroups": ["sg-0938cd187bc703883"],
            "EmrManagedSlaveSecurityGroup": "sg-06d8888d29c400604",
            "AdditionalSlaveSecurityGroups": ["sg-0938cd187bc703883"],
            "ec2_settings": {
                "bucket": "bucketplace-emr",
                "key": "settings/ec2_settings.json",
            },
        },
        "s3_path": {
            "application": "bucketplace-emr/data-batch/data-batch-assembly-0.1.0-SNAPSHOT.jar",
            "application-stage": "bucketplace-emr/data-batch-stage/data-batch-assembly-0.1.0-SNAPSHOT.jar",
            "log_uri": "bucketplace-emr/logs/",
            "appsflyer": "bucketplace-appsflyer",
            "athena-result": "bucketplace-emr/athena-result/",
            "ohs_logs": "bucketplace-hive/log/ohs_logs",
            "ohs_logs2": "bucketplace-hive/log/ohs_logs2",
            "stage_ohs_logs": "bucketplace-hive/log/stage_ohs_logs",
            "access_log": "ohouse-web-prod-access-log/AWSLogs/387471694114/elasticloadbalancing/ap-northeast-2",
        },
        "hive": {"test_db": "batch_test"},
    },
)


class AwsEmr(object):
    def __init__(
        self,
        name,
        no_core_instances=2,
        keep_job_flow_alive_when_no_steps=False,
        instance_type="xlarge",
        step_concurrency_level=1,
    ):
        self._name = name
        self._emr = None

        instances = aws.get("instances")

        ec2_setting = ec2.get(instance_type)

        log_uri = f"s3://{aws.get('s3_path')['log_uri']}"

        desired_capacity, weight = SparkConf.capacity_calculator(
            ec2_setting["InstanceType"]["name"], no_core_instances
        )

        self._job_flow = dict(
            Applications=[
                dict(Name="Hadoop"),
                dict(Name="Spark"),
                dict(Name="Hive"),
                dict(Name="JupyterEnterpriseGateway"),
            ],
            Configurations=[
                dict(
                    Classification="hive-site",
                    Properties={
                        "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
                    },
                ),
                dict(
                    Classification="spark-hive-site",
                    Properties={
                        "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
                    },
                ),
                dict(
                    Classification="spark-defaults",
                    Properties=SparkConf.generate_spark_conf(
                        ec2_setting["InstanceType"]["v_cpu"],
                        ec2_setting["InstanceType"]["ram"],
                        no_core_instances,
                    ),
                ),
            ],
            Instances=dict(
                InstanceFleets=[
                    dict(
                        Name="Master Fleet",
                        InstanceFleetType="MASTER",
                        TargetSpotCapacity=1,
                        InstanceTypeConfigs=list(
                            map(
                                lambda instance_type: dict(
                                    InstanceType=instance_type,
                                    WeightedCapacity=1,
                                    BidPriceAsPercentageOfOnDemandPrice=40.0,
                                ),
                                SparkConf.instance_pool("r5.xlarge"),
                            )
                        ),
                        LaunchSpecifications=dict(
                            SpotSpecification=dict(
                                TimeoutDurationMinutes=15,
                                TimeoutAction="SWITCH_TO_ON_DEMAND",
                            ),
                        ),
                    ),
                    dict(
                        Name="Core Fleet",
                        InstanceFleetType="CORE",
                        TargetSpotCapacity=desired_capacity,
                        InstanceTypeConfigs=list(
                            map(
                                lambda instance_type: dict(
                                    InstanceType=instance_type,
                                    WeightedCapacity=weight,
                                    BidPriceAsPercentageOfOnDemandPrice=40.0,
                                ),
                                SparkConf.instance_pool(
                                    ec2_setting["InstanceType"]["name"]
                                ),
                            )
                        ),
                        LaunchSpecifications=dict(
                            SpotSpecification=dict(
                                TimeoutDurationMinutes=15,
                                TimeoutAction="SWITCH_TO_ON_DEMAND",
                            ),
                        ),
                    ),
                ],
                KeepJobFlowAliveWhenNoSteps=keep_job_flow_alive_when_no_steps,
                TerminationProtected=True,
                Ec2SubnetId=instances["Ec2SubnetId"],
                EmrManagedMasterSecurityGroup=instances[
                    "EmrManagedMasterSecurityGroup"
                ],
                AdditionalMasterSecurityGroups=instances[
                    "AdditionalMasterSecurityGroups"
                ],
                EmrManagedSlaveSecurityGroup=instances["EmrManagedSlaveSecurityGroup"],
                AdditionalSlaveSecurityGroups=instances[
                    "AdditionalSlaveSecurityGroups"
                ],
            ),
            JobFlowRole="EMR_EC2_DefaultRole",
            StepConcurrencyLevel=step_concurrency_level,
            LogUri=log_uri,
            Name=name,
            ReleaseLabel="emr-6.3.0",
            ServiceRole="EMR_DefaultRole",
            Tags=[
                dict(Key="Owner", Value="Data"),
                dict(Key="Team", Value="Data"),
                dict(Key="Name", Value=name),
            ],
            VisibleToAllUsers=True,
        )

    @property
    def name(self):
        return self._name

    def get_emr(self):
        if self._emr is None:
            self._emr = boto3.client("emr")

        return self._emr

    def update_job_flow(self, new_dict):
        self._job_flow.update(new_dict)

    def get_job_flow_by_key(self, key):
        return self._job_flow.get(key)

    @property
    def keep_job_flow_alive_when_no_steps(self):
        return self._job_flow["Instances"]["KeepJobFlowAliveWhenNoSteps"]

    @property
    def application_path(self):
        if EnvSetting.is_production():
            return f"s3://{aws.get('s3_path')['application']}"
        else:
            return f"s3://{aws.get('s3_path')['application-stage']}"

    @classmethod
    def hive_production_db(cls):
        raise NotImplementedError

    @classmethod
    def hive_db(cls):
        if EnvSetting.is_production():
            return cls.hive_production_db()
        else:
            return aws.get("hive")["test_db"]

    def generate_step_list(self):
        raise NotImplementedError

    @property
    def max_time_in_seconds_to_wait(self):
        raise NotImplementedError

    def run(self):
        step_list = self.generate_step_list()
        steps_dict = dict(
            Steps=step_list,
        )
        self.update_job_flow(steps_dict)

        print(len(step_list), "steps will be launched.")

        response = self.get_emr().run_job_flow(**self._job_flow)

        cluster_id = Response.read_cluster_id(response)
        if cluster_id is None:
            return CODE_CANNOT_READ_CLUSTER_ID

        num_steps_for_starting = int(MAX_TIME_WAIT_FOR_STARTING / SLEEP_IN_SECONDS)
        for _ in range(num_steps_for_starting):
            response = self.get_emr().describe_cluster(ClusterId=cluster_id)
            state = Response.read_state(response)
            if state is None:
                return CODE_CANNOT_READ_STATE

            print("State: " + state)
            if state not in set(["STARTING"]):
                print("STARTING is over.")
                break

            sleep(SLEEP_IN_SECONDS)

        num_steps = int(self.max_time_in_seconds_to_wait / SLEEP_IN_SECONDS)
        for _ in range(num_steps):
            response = self.get_emr().describe_cluster(ClusterId=cluster_id)
            state = Response.read_state(response)
            if state is None:
                return CODE_CANNOT_READ_STATE

            if self.keep_job_flow_alive_when_no_steps and state in set(
                ["WAITING", "RUNNING"]
            ):
                return CODE_SUCCESS

            elif not self.keep_job_flow_alive_when_no_steps and state in set(
                ["TERMINATED", "TERMINATED_WITH_ERRORS"]
            ):
                termination_code = Response.read_termination_code(response)
                if termination_code is None:
                    return CODE_CANNOT_READ_TERMINATION_CODE

                print("Termination code: " + termination_code)
                if state == "TERMINATED" and termination_code == "ALL_STEPS_COMPLETED":
                    return CODE_SUCCESS
                else:
                    return CODE_FAILURE

            elif not self.keep_job_flow_alive_when_no_steps and state in set(
                ["TERMINATING"]
            ):
                termination_code = Response.read_termination_code(response)
                if termination_code is None:
                    pass
                if termination_code == "ALL_STEPS_COMPLETED":
                    return CODE_SUCCESS
                else:
                    return CODE_FAILURE

            else:
                print("State: " + state)

            sleep(SLEEP_IN_SECONDS)

        return CODE_REACH_TO_MAX_TIME

    def print_job_flow(self):
        import pprint

        pprint.pprint(self._job_flow, width=1)

    def get_cluster_id_by_name(self, cluster_name, cluster_states) -> str:
        response = self.get_emr().list_clusters(ClusterStates=cluster_states)

        matching_clusters = list(
            filter(
                lambda cluster: cluster["Name"] == cluster_name, response["Clusters"]
            )
        )

        if len(matching_clusters) == 1:
            cluster_id = matching_clusters[0]["Id"]
            print(f"Found cluster name = {cluster_name} id = {cluster_id}")
            return cluster_id
        elif len(matching_clusters) > 1:
            raise Exception(f"More than one cluster with name {cluster_name}")
        else:
            raise Exception(f"No cluster found with name : {cluster_name}")

    def add_jobs(self):
        """
        Will add jobs to running cluster or start a new cluster to run jobs.
        Depends on cluster name to find cluster.
        By default add_jobs will always set KeepJobFlowAliveWhenNoSteps to True when
        starting a new cluster.
        Using add_jobs instead of run will keep the cluster alive, will track each
        added step individually instead of tracking the cluster by using list_jobs
        instead of describe cluster.
        """
        try:
            cluster_id = self.get_cluster_id_by_name(
                self._name, ["STARTING", "BOOTSTRAPPING", "RUNNING", "WAITING"]
            )
        except Exception as e:
            print(e)
            if not self.keep_job_flow_alive_when_no_steps:
                print("Will change KeepJobFlowAliveWhenNoSteps True")
                self._job_flow["Instances"]["KeepJobFlowAliveWhenNoSteps"] = True

            print(f"Starting cluster {self._name}")
            cluster_res = self.get_emr().run_job_flow(**self._job_flow)

            cluster_id = Response.read_cluster_id(cluster_res)
            if cluster_id is None:
                return CODE_CANNOT_READ_CLUSTER_ID

        step_list = self.generate_step_list()

        res = self.get_emr().add_job_flow_steps(
            JobFlowId=cluster_id,
            Steps=step_list,
        )
        # list_steps can only show up to 10 steps
        step_ids = [
            res["StepIds"][x: x + 10] for x in range(0, len(res["StepIds"]), 10)
        ]

        print(f"{len(step_list)} steps will be launched in cluster {self._name}.")

        num_steps = int(self.max_time_in_seconds_to_wait / SLEEP_IN_SECONDS)
        for _ in range(num_steps):
            states = list()
            failures = list()

            for steps in step_ids:
                response = self.get_emr().list_steps(
                    ClusterId=cluster_id, StepIds=steps
                )
                for step in response["Steps"]:
                    status = step["Status"]["State"]
                    states.append(status)
                    if status == "FAILED" or status == "CANCELLED":
                        failures.append(step["Name"])

            if "RUNNING" in set(states) or "PENDING" in set(states):
                sleep(SLEEP_IN_SECONDS)
            else:
                print(f"States: {', '.join(states)}")
                if len(failures) > 0:
                    print(f"Failures in steps:{', '.join(failures)}")
                    return CODE_FAILURE
                else:
                    return CODE_SUCCESS

            print(f"States: {', '.join(states)}")

        return CODE_REACH_TO_MAX_TIME
