from django.http import HttpResponse
from django.contrib.auth.models import Group


def number_of_queries_to_run_view(request, nr_of_queries):
    nr_of_queries = int(nr_of_queries)
    assert nr_of_queries >= 0
    for i in range(nr_of_queries):
        list(Group.objects.all())
    return HttpResponse('Executed {} queries'.format(nr_of_queries))
