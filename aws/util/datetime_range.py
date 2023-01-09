import datetime


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class DateTimeRange(object):
    def __init__(self, datetime_from_str, datetime_to_str):
        def parse_datetime_str(datetime_str):
            try:
                return datetime.datetime.strptime(datetime_str, DATETIME_FORMAT)
            except ValueError:
                return None

        datetime_from = parse_datetime_str(datetime_from_str)
        datetime_to = parse_datetime_str(datetime_to_str)

        self._datetimes = list()
        
        date_delta = datetime_to - datetime_from
        for i in range(int(date_delta.total_seconds()) // 3600 + 1):
            curr_datetime = datetime_from + datetime.timedelta(hours=i)
            curr_datetime_str = curr_datetime.strftime(DATETIME_FORMAT)
            self._datetimes.append(curr_datetime_str)

    @property
    def datetime_list(self):
        return self._datetimes

    @property
    def hours(self):
        return len(self._datetimes)

    @property
    def first_datetime(self):
        return self._datetimes[0]

    @property
    def last_datetime(self):
        return self._datetimes[-1]
