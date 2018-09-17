import holidays

from .matcher import matchers


class EstG3b:
    def __init__(self, country: str = 'DE', add_matchers=None, replace_matchers=None) -> None:
        if country:
            country = country.upper()
            self._machers = matchers[country]
            self._holidays = holidays.CountryHoliday(country)
        else:
            self._machers = []

        if replace_matchers:
            self._matchers = replace_matchers.copy()
        if add_matchers:
            self._machers.extend(add_matchers)

        assert self._matchers
