==========================
django-performance-testing
==========================

.. image:: https://travis-ci.org/PaesslerAG/django-performance-testing.svg?branch=master
        :target: https://travis-ci.org/PaesslerAG/django-performance-testing

.. contents:: Performance testing for Django through your automated tests!

Don't leave performance testing until the end of the project! We have learned
already that more frequent feedback on smaller chunks of changes is much better,
e.g.: TDD, CI, DevOps, Agile, etc.

This library helps by providing performance testing from the start -
integrating it seemlessy into your existing development cycle, without
requiring changes to your development workflow.

Unlike regular performance testing tools (``ab``, ``tsung``, etc.), this
libary relies on indirect (proxy) indicators to performence - e.g.: the number
of queries executed. It's a good rule of thumb that the more SQL there is, the
slower it will be. And this way "performance" testing won't be slower than your
normal tests! (Disclimer: while this tool is useful, classic performance
testing is still recommended!)


Setup
=====

* install it via ``pip install django-performance-testing``
* add it to your settings and it auto-registers itself
  ::

      settings.INSTALLED_APPS = [
         ...
         'django_performance_testing',
         ...
      ]
* set your limits (see below for detail)
* and run your test ``manage.py test <your app>``

For any limit violations, there will be a test failure, and at the end, a
`Worst Items Report` will be printed.

Supported Limits
================

Querycount
----------

Sets the limit in the number of queries executed inside the given scope.
Limits can be set for the ``total`` number of queries, or more specifically,
based on types of queries - ``read`` (``SELECT``), ``write`` (
``INSERT``, ``UPDATE``, ``DELETE``), and ``other`` (e.g.:
transaction (savepoints)).

When no (or ``None``) value is provided for a given limit type, that is 
ignored during the check, as if there were no limit rules for. Thus it's 
possible to only focus on no write queries, while ignoring all the other queries
that might be executed.

Setting Limits
==============

Predefined limit points
-----------------------

Following are the keys that are currently supported for
``settings.PERFORMANCE_LIMITS`` dictionary

* ``django.test.client.Client`` - every call to its ``request`` method
  is limited, i.e.: ``GET``, ``POST``, etc.
* ``Template.render`` - every ``render`` call is checked for limits.
  Note: it's   recursive, i.e.: `include` and similar tags result in a check
* ``test method`` - the actual various ``unittest`` test methods that
  you write for your app

And the following types of limits are supported:

  * ``queries`` - contains the values for query count limits, such as
    ``read``, ``write``, ``other``, ``total``
  * ``time`` - can specify a limit for the ``total`` elapses seconds for the
    given limit point

Sample Settings
---------------

::

    PERFORMANCE_LIMITS = {
        'test method': {
            'queries': {'total': 50},  # want to keep the tests focused
            'time': {'total': 0.2},  # want fast integrated tests, so aiming for 1/5 seconds
        },
        'django.test.client.Client': {
            'queries': {
                'read': 30,
                'write': 8,  # do not create complex object structures in the web
                             # process
            },
        },
        'Template.render': {
            'queries': {
                'write': 0,  # rendering a template should never write to the database!
                'read': 0
            }
        }
    }

Ad-Hoc Limits
=============

While the builtin measurement points are great, sometimes, when profiling
and trying to improve sections of the code, more granular limits are needed.
To support that, the limits can be used as context managers, e.g.:


::

    from django_performance_testing.queries import QueryBatchLimit
    from django_performance_testing.timing import TimeLimit
    ...
    
    def my_method_with_too_many_queries(request):
        with QueryBatchLimit(write=0, read=10):  # initialize form
            form = MyForm(request.POST)
        with QueryBatchLimit(write=0, read=3):  # validate it
            is_valid = form.is_valid()
        if is_valid:
            with QueryBatchLimit(read=0, write=8):  # save it
                form.save()
            with QueryBatchLimit(read=0, write=0):  # redirect
                return HttpResponseRedirect(...)
        else:
            with QueryBatchLimit(write=0):  # render form
                with TimeLimit(total=0.01):   # we need superfast templates
                    return form_invalid(form)

Release Notes
=============

* 0.2.0

  * add timing measurement that can be limited
  * remove uniqueness check for ``collector.id_``, as the problems it caused
    for testing outweighed its benefit for developer debugging aid
  * backwards incompatible:

    * change how settings based limits are specified
    * change the worst report data output/data structure

* 0.1.1 - bugfix release

  * bugfix: attributes set by on test methods (e.g.: ``@unittest.skip``)
    are now recognizable again and not lost due to the library's patching

* 0.1.0 - initial release

  * supports Django 1.8, 1.9, 1.10 on python 2.7, 3.3, 3.4, and 3.5
  * query counts are reported and can be limited, by categories -
    ``read``, ``write``, ``other``, and ``total`` 
  * support ad-hoc limits by using it as a context manager
  * predefined limits support:

    * ``django.test.client.Client`` - all calls to its request method
    * actual ``unittest`` ``test_<foo>`` methods
    * ``Template.render``

.. contributing start

Contributing
============

As an open source project, we welcome contributions.

The code lives on `github <https://github.com/PaesslerAG/django-performance-testing>`_.

Reporting issues/improvements
-----------------------------

Please open an `issue on github <https://github.com/PaesslerAG/django-performance-testing/issues/>`_
or provide a `pull request <https://github.com/PaesslerAG/django-performance-testing/pulls/>`_
whether for code or for the documentation.

For non-trivial changes, we kindly ask you to open an issue, as it might be rejected.
However, if the diff of a pull request better illustrates the point, feel free to make
it a pull request anyway.

Pull Requests
-------------

* for code changes

  * it must have tests covering the change. You might be asked to cover missing scenarios
  * the latest ``flake8`` will be run and shouldn't produce any warning
  * if the change is significant enough, documentation has to be provided

Setting up all Python versions
------------------------------

::

    sudo apt-get -y install software-properties-common
    sudo add-apt-repository ppa:fkrull/deadsnakes
    sudo apt-get update
    for version in 3.3 3.5; do
      py=python$version
      sudo apt-get -y install ${py} ${py}-dev
    done

Code of Conduct
---------------

As it is a Django extension, it follows
`Django's own Code of Conduct <https://www.djangoproject.com/conduct/>`_.
As there is no mailing list yet, please just email one of the main authors
(see ``setup.py`` file or `github contributors`_)


.. contributing end


.. _github contributors: https://github.com/PaesslerAG/django-performance-testing/graphs/contributors
