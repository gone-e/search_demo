# Refer to https://aws.amazon.com/ko/blogs/big-data/best-practices-for-successfully-managing-memory-for-apache-spark-applications-on-amazon-emr/
class SparkConf(object):
    @staticmethod
    def calculated_executor_cores(v_cpu):
        if v_cpu >= 11:
            # we suggest that you have five virtual cores for each executor to achieve optimal results in any sized cluster.
            return 5
        else:
            # not to use too small # of executors per instance
            return 3

    @classmethod
    def generate_spark_conf(cls, v_cpu, ram, no_core_instances):
        executor_cores = cls.calculated_executor_cores(v_cpu)

        no_executor_per_instances = int((v_cpu - 1) / executor_cores)
        total_executor_memory = int(ram / no_executor_per_instances)

        executors_memory = int(total_executor_memory * 0.68)

        executor_instances = (no_executor_per_instances * no_core_instances) - 1

        default_parallelism = executor_instances * executor_cores * 2

        return {
            "spark.executor.cores": str(executor_cores),
            "spark.driver.cores": str(executor_cores),
            "spark.executor.memory": f"{str(executors_memory)}G",
            "spark.driver.memory": f"{str(executors_memory)}G",
            "spark.executor.instances": str(executor_instances),
            "spark.default.parallelism": str(default_parallelism),
            "spark.yarn.executor.memoryOverheadFactor": "0.1",
            "spark.sql.broadcastTimeout": "3600",
            "spark.driver.maxResultSize": "0",
        }

    @classmethod
    def capacity_calculator(cls, instance_type, count):
        """
            params:
                instance_type: Aws Instance Spec. t2.medium, r5.large, r5.4xlage
                count: desired instance count
            return:
                capacity: calculated instance fleet capacity. if spec under xlage, use simply count as capacity.
                weight: capacity per one instance
        """

        _, spec = instance_type.split(".")

        if "xlarge" != spec:
            weight = int(spec[0])
            return weight * count, weight
        else:
            return count, 1

    @classmethod
    def instance_pool(cls, instance_type):
        """
            params:
                instance_type: Aws Instance Spec. t2.medium, r5.large, r5.4xlarge
            return:
                instance_pool with same instance specs. handle only for "r" type
        """
        prefix = ["r5", "r5a", "r5d", "r4"]
        generation, spec = instance_type.split(".")

        if "r" in generation and "xlarge" in spec:
            return list(map(lambda gen_prefix: f"{gen_prefix}.{spec}", prefix))
        else:
            return [instance_type]
