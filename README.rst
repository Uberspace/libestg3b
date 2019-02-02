libestg3b
#########

.. image:: https://travis-ci.com/Uberspace/libestg3b.svg?branch=master
    :target: https://travis-ci.com/Uberspace/libestg3b
    :alt: CI Status

.. image:: https://readthedocs.org/projects/libestg3b/badge/?version=latest
    :target: https://libestg3b.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/libestg3b.svg
    :target: https://pypi.python.org/pypi/libestg3b
    :alt: PyPI

§ 3b of the German Einkommensteuergesetz (EStG) defines the premiums for work on
weekends, holidays and special days, like new year. This library takes a list of
work hours / shifts (e.g. on 2018-06-03 from 19:00 until 03:00) and returns the
premium factor (e.g. 1.5) as well as the relevant time-spans.

As noted in the license, this software is provided without any warranty or
guarantee for correctness.

§ 3b des Deutschen Einkommensteuergesetzes (EStG) definiert die Höhe der
steuerfreien Zuschläge für Arbeit in der Nacht, an Sonntagen, Feiertagen sowie
besonderen Tagen wie Neujahr. Diese Library errechnet aus einer Liste von
Arbeitszeiten die Höhe der maximalen Zuschläge.

Diese Software wird, wie in der Lizenz angegeben, ohne Gewähr und Garantie
auf Richtigkeit bereitgestellt.

Installation
------------

Install libestg3b via pip:

.. code-block:: console

    $ pip install libestg3b

Usage
-----

.. code-block:: pycon

    >>> import datetime as DT
    >>> from libestg3b import EStG3b
    >>> e = EStG3b('DE')()
    >>> e.calculate_shift([datetime(2018, 9, 16, 20), datetime(2018, 9, 17, 2)])
    [
        Match(
            start=datetime.datetime(2018, 9, 16, 19, 0),
            end=datetime.datetime(2018, 9, 16, 20, 0),
            rules={<Rule: Sonntagsarbeit>}
        ),
        Match(
            start=datetime.datetime(2018, 9, 16, 20, 0),
            end=datetime.datetime(2018, 9, 17, 0, 0),
            rules={<Rule: Sonntagsarbeit>, <Rule: Nachtarbeit 20:00-06:00>}
        ),
        Match(
            start=datetime.datetime(2018, 9, 17, 0, 0),
            end=datetime.datetime(2018, 9, 17, 2, 0),
            rules={<Rule: Sonntagsarbeit (Montag)>, <Rule: Nachtarbeit 00:00-04:00 (Folgetag)>}
        ),
    ]

Development
-----------

Setup
^^^^^

Using python 3.6, do the following:

.. code-block:: console

    $ virtualenv venv --python=python3.6
    $ pip install -e ".[dev]"

Usual Tasks
^^^^^^^^^^^

* ``make test``: run tests (use ``tox`` or ``py.test`` directly to supply flags like ``-k``)
* ``make lint``: run pylava and friends
* ``make fixlint``: sort imports correctly

Releasing a new version
^^^^^^^^^^^^^^^^^^^^^^^

Assuming you have been handed the required credentials, a new version
can be released as follows.

1. adapt the version in ``setup.py``, according to `semver`_.
2. commit this change as ``Version 1.2.3``
3. tag the resulting commit as ``v1.2.3``
4. push the new tag as well as the ``master`` branch
5. update the package on PyPI:

.. code-block:: console

    $ rm dist/*
    $ python setup.py sdist bdist_wheel
    $ twine upload dist/*

Prerequisites
-------------

This library is currently python 3.6+. If you would like to use this library
with a lower python version, please open an issue. We're happy to change things
around.

Versioning
----------

New version numbers are assigned following `semver`_. All
0.x.y versions are tested and usable, but do not have a stable public interface.

A version 1.0 will be released, once we deem the library stable.

License
-------

All code in this repository is licensed under the MIT license.

.. _semver: http://semver.org/
