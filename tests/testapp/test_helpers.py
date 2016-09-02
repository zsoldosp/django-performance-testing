from django.utils import six
from collections import namedtuple


WithId = namedtuple('WithId', ('id_',))


def run_django_testcase(testcase_cls, django_runner_cls):
    django_runner = django_runner_cls()
    suite = django_runner.test_suite()
    tests = django_runner.test_loader.loadTestsFromTestCase(testcase_cls)
    suite.addTests(tests)
    test_runner = django_runner.test_runner(
        resultclass=django_runner.get_resultclass(),
        stream=six.StringIO()
    )
    result = test_runner.run(suite)
    return dict(
        django_runner=django_runner,
        suite=suite,
        test_runner=test_runner,
        result=result,
        out=result.stream.getvalue()
    )
