from .estg3b import EStG3bBase, Match
import libestg3b.countries as countries
from typing import Type, List
import inspect


def EStG3b(country: str) -> Type[EStG3bBase]:
    """
    Get the implementation class for the given country.

    :param country: ISO short code of the desired country, e.g. ``"DE"``
    """

    country = country.upper()

    try:
        return next(c for c in EStG3bs() if country in c.aliases)
    except StopIteration:
        raise KeyError("Country %s not available" % country)


def EStG3bs() -> List[Type[EStG3bBase]]:
    """
    Get a list containing implementation classes for all implemented countries.
    """
    return [
        clazz
        for clazz in map(lambda a: getattr(countries, a), dir(countries))
        if inspect.isclass(clazz) and issubclass(clazz, EStG3bBase) and clazz != EStG3bBase
    ]


__all__ = [
  "EStG3b",
  "EStG3bs",
  "EStG3bBase",
  "Match",
]
