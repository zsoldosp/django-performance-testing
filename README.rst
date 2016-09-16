===========================
django-performance-testing
==========================

Performance testing for Django through your automated tests.

Don't leave performance testing until the end of the project! We have learned
already that more frequent feedback on smaller chunks of changes is much better,
e.g.: TDD, CI, DevOps, Agile, etc.

This library helps by providing performance testing from the start -
integrating it seemlessy into your existing development cycle, without
requiring changes to your development workflow.

Unlike regular performance testing tools (`ab`, `tsung`, etc.), this libary
relies on indirect (proxy) indicators to performence - e.g.: the number of
queries executed. It's a good rule of thumb that the more SQL there is, the
slower it will be. And this way "performance" testing won't be slower than your
normal tests! (Disclimer: while this tool is useful, classic performance
testing is still recommended!)


Setup
=====

* install it via `pip install django-performance-testing`
* add it to your settings
  ```
  settings.INSTALLED_APPS = [
     ...
     'django_performance_testing',
     ...
  ]
  ```
  and it auto-registers itself
* set your limits (see below for detail)
* and run your test `manage.py tes <your app>`

For any limit violations, there will be a test failure, and at the end, a
_Worst Items Report_ will be printed.

Supported Limits
================

Querycount
----------

Sets the limit in the number of queries executed inside the given scope.
Limits can be set for the `total` number of queries, or more specifically,
based on types of queries - `read` (`SELECT`), `write` (`INSERT`, `UPDATE`,
`DELETE`), and `other` (e.g.: transaction (savepoints)).

When no (or `None`) value is provided for a given limit type, that is ignored
during the check, as if there were no limit rules for. Thus it's possible to only
focus on no write queries, while ignoring all the other queries that might be
executed.

Setting Limits
==============

Predefined limit points
-----------------------

Following are the keys that are currently supported for
`settings.PERFORMANCE_LIMITS` dictionary

* `django.test.client.Client` - every call to its `request` method is limited,
  i.e.: `GET`, `POST`, etc.
* `Template.render` - every `render` call is checked for limits. Note: it's
  recursive, i.e.: `include` and similar tags result in a check
* `test method` - the actual various `unittest` test methods that you write
  for your app

Sample Settings
---------------

```
PERFORMANCE_LIMITS = {
    'test method': {'total': 50},  # want to keep the tests focused
    'django.test.client.Client': {
        'read': 30,
        'write': 8,  # do not create complex object structures in the web
                     # process

    },
    'Template.render': {
        'write': 0,  # rendering a template should never write to the database!
        'read': 0
    }
}
```

Ad-Hoc Limits
=============

While the builtin measurement points are great, sometimes, when profiling
and trying to improve sections of the code, more granular limits are needed.
To support that, the limits can be used as context managers, e.g.:


```
from django_performance_testing.queries import QueryBatchLimit
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
            return form_invalid(form)
```

Infrastructure links
====================

* `CI Builder`_
* the package on  `PyPi`_
* the  `Git repo`_

Release Notes
=============

* 0.1.0 - initial release

  * supports Django 1.8, 1.9, 1.10 on python 2.7 and 3.4
  * query counts are reported and can be limited, by categories -
    `read`, `write`, `other`, and `total` 
  * support ad-hoc limits by using it as a context manager
  * predefined limits support:

    * `django.test.client.Client` - all calls to its request method
    * actual `unittest` `test_<foo>` methods
    * `Template.render`


.. _CI Builder: https://travis-ci.com/PaesslerAG/django-performance-testing
.. _PyPi: http://pypi.python.org/simple/django-performance-testing
.. _Git: https://github.com/PaesslerAG/django-performance-testing
