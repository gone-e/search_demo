from aws.emr.aws_emr import AwsEmr
from aws.util.date_range import DateRange


class AwsEmrDateRange(AwsEmr):
    def __init__(self, name, date_from, date_to, no_core_instances=2, instance_type="xlarge"):
        super().__init__(name, no_core_instances=no_core_instances, instance_type=instance_type)

        self._date_range = DateRange(date_from, date_to)

    @property
    def max_time_in_seconds_to_wait(self):
        return self._date_range.days * 30 * 60

    @property
    def date_list(self):
        return self._date_range.date_list

    @property
    def days(self):
        return self._date_range.days

    @property
    def first_date(self):
        return self._date_range.first_date

    @property
    def last_date(self):
        return self._date_range.last_date
