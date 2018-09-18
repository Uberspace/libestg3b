# libestg3b

§ 3b of the german Einkommensteuergesetz (EStG) defines the premiums for work on
weekends, holidays and special days, like new year. This library takes a list of
work hours / shifts (e.g. on 2018-06-03 from 19:00 until 03:00) and returns the
premium factor (e.g. 1.5) as well as the relevant timespans.

§ 3b des Deutschen Einkommensteuergesetzes (EStG) definiert die Höhe der
steuerfreien Zuschläge für Arbeit in der Nacht, an Sonntagen, Feiertagen sowie
besondere Tage wie Neujahr. Diese Library erreichnet aus einer Liste von
Arbeitszeiten die höhe der maximalen Zuschläge.

## Installation

Install libestg3b via pip:

```
$ pip install libestg3b
```

## Usage

```pycon
>>> import datetime as DT
>>> from libestg3b import EstG3b
>>> e = EstG3b('DE')
>>> e.calculate_shift([datetime(2018, 9, 16, 20), datetime(2018, 9, 17, 2)])
[
    Match(
        start=datetime.datetime(2018, 9, 16, 19, 0),
        end=datetime.datetime(2018, 9, 16, 20, 0),
        matchers={<Matcher: Sonntagsarbeit>}
    ),
    Match(
        start=datetime.datetime(2018, 9, 16, 20, 0),
        end=datetime.datetime(2018, 9, 17, 0, 0),
        matchers={<Matcher: Sonntagsarbeit>, <Matcher: Nachtarbeit 20:00-06:00>}
    ),
    Match(
        start=datetime.datetime(2018, 9, 17, 0, 0),
        end=datetime.datetime(2018, 9, 17, 2, 0),
        matchers={<Matcher: Sonntagsarbeit (Montag)>, <Matcher: Nachtarbeit 00:00-04:00 (Folgetag)>}
    ),
]
```

## Prerequisites

This library is currently python 3.7 only. If you would like to use this library
with a lower python version, please open an issue. We're happy to change things
around.

## Versioning

New version numbers are assigned following [semver](http://semver.org/). All
0.x.y versions are tested and usable, but do not have a stable public interface.

A version 1.0 will be released, once we deem the library stable.

## Releasing a new version

Assuming you have been handed the required credentials, a new version
can be released as follows.

1. adapt the version in `setup.py`, according to [semver](http://semver.org/)
2. commit this change as `Version 1.2.3`
3. tag the resulting commit as `v1.2.3`
4. push the new tag as well as the `master` branch
5. update the package on PyPI:

```
rm dist/*
python setup.py sdist bdist_wheel
twine upload dist/*
```

# License

All code in this repository is licensed under the MIT license.
