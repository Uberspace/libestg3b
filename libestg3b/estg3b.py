import datetime
import itertools

import holidays
from dateutil.relativedelta import relativedelta

from .matcher import Match, matchers


class EstG3b:
    def __init__(self, country: str = 'DE', add_matchers=None, replace_matchers=None) -> None:
        if country:
            country = country.upper()
            self._matchers = matchers[country]
            self._holidays = holidays.CountryHoliday(country)
        else:
            self._machers = []

        if replace_matchers:
            self._matchers = replace_matchers.copy()
        if add_matchers:
            self._machers.extend(add_matchers)

        assert self._matchers

    def _list_minutes(self, start, end):
        start = start.replace(second=0, microsecond=0)
        end = end.replace(second=0, microsecond=0)

        while start < end:
            yield start
            start = start + relativedelta(minutes=1)

    def calculate_shift(self, shift):
        assert len(shift) == 2
        assert isinstance(shift[0], datetime.datetime)
        assert isinstance(shift[1], datetime.datetime)

        minutes = self._list_minutes(shift[0], shift[1])
        first_minute = next(minutes)
        minutes = itertools.chain([first_minute], minutes)

        matches = []

        for minute in minutes:
            minute_matchers = []

            # find the highest matcher for each group (if any) and save it
            for group in self._matchers:
                try:
                    minute_matchers.append(max([
                        matcher for matcher in group
                        if matcher(minute, first_minute, self._holidays)
                    ]))
                except ValueError:  # no match found
                    pass

            # combine equal matches by increasing the length of the last one
            if matches and matches[-1].matchers == minute_matchers:
                matches[-1].end = matches[-1].end + relativedelta(minutes=1)
            else:
                matches.append(Match(minute, minute, minute_matchers))

        return matches

    def calculate_shifts(self, shifts):
        return map(self.calculate_shift, shifts)
