adding rules
============

Most companies just follow the law when it comes to paying bonuses for work on
weekends. Libestg3b comes with a standard set of rules to cover that use case.
It is, howerver, also possible to extend the Rules to match your situation. This
enables you to define special situations like "12-12 is our annual christmas
party, pay 100% extra for any shifts during that".

Defining it
-----------

Rules are implemented using :class:`~libestg3b.rule.Rule` objects. They contain
all neccesary information like the rules name, when to apply it and what do to,
when it does.

.. code-block:: python

    from decimal import Decimal
    from libestg3b.rule import Rule

    r = Rule(
        "CHRISTMAS_PARTY",
        "Annual company christmas party",
        lambda minute, start, holidays: minute.month == 12 and minute.day == 12,
        multiply=Decimal(1),
    )

We've got a rule! Most of this should be pretty easy to understand, but the
lambda in there can raise some questions, so let's go over it: The function you
pass into the constructor is the actual implementation of your rule. It defines
when to apply it. To make sure it's able to do its job, a couple of data points
are passed into it:

* ``minute`` (``datetime``)

Also refer to :meth:`libestg3b.rule.Rule.match` for further information and
examples.

Boiling it down
^^^^^^^^^^^^^^^

Writing a lambda function for each rule you want to write is fun, but generates
a lot of boilerplate code. Since many rules are quite repetitive ("match on some
date", "match after some time", ...), libestg3b comes with a couple of helpers
to save you some time:

* :class:`~libestg3b.rule.DayRule`: match on a given month/day combination (e.g. YYYY-03-28)
* :class:`~libestg3b.rule.DayTimeRule`: like :class:`~libestg3b.rule.DayRule`, but also require the shift to be after a certain time (e.g. 14:00).

Documentation and examples on these classes can be found in the respective class
docs (follow the link, alice!). To clear things up a bit, have a look at the
following example on how to shorten our ``CHRISTMAS_PARTY`` rule using the
``DayRule`` class:

.. code-block:: python

    from decimal import Decimal
    from libestg3b.rule import DayRule

    r = DayRule("CHRISTMAS_PARTY", 12, 12, multiply=Decimal(1))


Except for the imports, we can now even fit it into one line without feeling bad.


Plugging it in
--------------

Feel floating rule objects are great, but they don't do much. To convince the
library to actually use your rules to match shifts, we need to tell it about
them:

.. code-block:: python

    from decimal import Decimal
    from libestg3b import EStG3b
    from libestg3b.rule import DayRule, RuleGroup

    est = EStG3b("DE")(add_rules=[
        RuleGroup(
            "GRP_CUSTOM",
            "Rules special to our company",
            [DayRule("CHRISTMAS_PARTY", 12, 12, multiply=Decimal(1))],
        )
    ])

You'll quickly notice a new thing here: Groups.

A :class:`libestg3b.rule.RuleGroup` is a set of rules of which only one may ever
match. A pratical example of why this might be useful is outlined in German law:
there is night work (+25%), work on sundays (+50%) and work on holidays (+125%).
While work during sunday nights allows combining the rules to yield +175%, work
on sundays, which happen to be a holiday, only allows one of the rules to be
applied, resulting in +125%. In case two or more rules match, group chooses the
one with the highest bonus and discards all other matches.

Since all rules need to be in a group, we just make up a new one (``GRP_CUSTOM``)
with nothing in it except for our special rule. This allows it to be matched in
addition to any other rules already predefined by law.

Running it
----------

We've got a rule, we've told the library about it, let's see, if it actually
works. Make up a shift from 12-12 19:00 until 01:00 the next day, plug it into
``calculate_shift`` as outlined in  :doc:`the first guide </how_to_use>` and run
it:

.. code-block:: python

    ...

    import datetime as DT

    m = est.calculate_shift([DT.datetime(2018, 12, 12, 19), DT.datetime(2018, 12, 13, 1)])
    print(m)

.. code-block:: text

    [
        <Match 2018-12-12T19:00~2018-12-12T20:00, CHRISTMAS_PARTY, add=0, multiply=1>,
        <Match 2018-12-12T20:00~2018-12-13T00:00, CHRISTMAS_PARTY+DE_NIGHT, add=0, multiply=1.25>,
        <Match 2018-12-13T00:00~2018-12-13T01:00, DE_NIGHT_START_YESTERDAY, add=0, multiply=0.4>
    ]

As you can see, our rule worked just as intended. In addition to the predefined
``DE_NIGHT`` rules, there is now also a match for ``CHRISTMAS_PARTY`` during the
relevant times.

Happy matching!
