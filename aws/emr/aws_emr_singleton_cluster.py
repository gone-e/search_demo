from aws.emr.aws_emr import AwsEmr, CODE_SUCCESS
from aws.util.date_range import DateRange


class AwsEmrSingletonCluster(AwsEmr):
    def _get_cluster_ids_by_states(self, states):
        cluster_list = self.get_emr().list_clusters(ClusterStates=states)["Clusters"]
        return [cluster["Id"] for cluster in cluster_list]

    def _get_active_cluster_ids(self):
        return self._get_cluster_ids_by_states(["STARTING", "BOOTSTRAPPING", "RUNNING", "WAITING"])

    def _filter_cluster_ids_by_tag_name(self, cluster_ids, name_tag_list):
        filtered_cluster_ids = list()
        for cluster_id in cluster_ids:
            cluster = self.get_emr().describe_cluster(ClusterId=cluster_id)["Cluster"]
            tag_dict = dict((tag["Key"], tag["Value"]) for tag in cluster["Tags"])

            if tag_dict.get("Name") == name_tag_list:
                filtered_cluster_ids.append(cluster_id)

        return filtered_cluster_ids

    def _filter_cluster_ids_by_tag_name_prefix(self, cluster_ids, name_prefix):
        filtered_cluster_ids = list()
        for cluster_id in cluster_ids:
            cluster = self.get_emr().describe_cluster(ClusterId=cluster_id)["Cluster"]
            tag_dict = dict((tag["Key"], tag["Value"]) for tag in cluster["Tags"])

            if "Name" in tag_dict and tag_dict["Name"].startswith(name_prefix):
                filtered_cluster_ids.append(cluster_id)

        return filtered_cluster_ids

    def _terminate_clusters_by_ids(self, cluster_ids):
        if len(cluster_ids) > 0:
            self.get_emr().set_termination_protection(JobFlowIds=cluster_ids, TerminationProtected=False)
            self.get_emr().terminate_job_flows(JobFlowIds=cluster_ids)

    def run_if_not_running(self):
        active_cluster_ids = self._get_active_cluster_ids()
        active_zeppelin_cluster_ids = self._filter_cluster_ids_by_tag_name(active_cluster_ids, self.name)

        if len(active_zeppelin_cluster_ids) == 0:
            return self.run()
        else:
            print("The following clusters are running:")
            print(", ".join(map(str, active_zeppelin_cluster_ids)))
            return CODE_SUCCESS

    def terminate_all_by_name_prefix(self, name_prefix):
        active_cluster_ids = self._get_active_cluster_ids()
        active_zeppelin_cluster_ids = self._filter_cluster_ids_by_tag_name_prefix(active_cluster_ids, name_prefix)

        print("The following clusters will be terminated:")
        print(", ".join(map(str, active_zeppelin_cluster_ids)))

        self._terminate_clusters_by_ids(active_zeppelin_cluster_ids)
