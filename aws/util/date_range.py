import datetime


DATETIME_FORMAT = "%Y-%m-%d"


class DateRange(object):
    def __init__(self, date_from_str, date_to_str):
        def parse_date_str(date_str):
            try:
                return datetime.datetime.strptime(date_str, DATETIME_FORMAT)
            except ValueError:
                return None

        date_from = parse_date_str(date_from_str)
        date_to = parse_date_str(date_to_str)

        self._dates = list()
        
        date_delta = date_to - date_from
        for i in range(date_delta.days + 1):
            curr_date = date_from + datetime.timedelta(days=i)
            curr_date_str = curr_date.strftime(DATETIME_FORMAT)
            self._dates.append(curr_date_str)

    @property
    def date_list(self):
        return self._dates

    @property
    def days(self):
        return len(self._dates)

    @property
    def first_date(self):
        return self._dates[0]

    @property
    def last_date(self):
        return self._dates[-1]
