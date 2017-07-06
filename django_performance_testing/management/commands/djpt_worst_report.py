from django.core.management.base import BaseCommand
from django_performance_testing.reports import WorstReport
from django_performance_testing.serializer import \
    get_datafile_path, Reader


class Command(BaseCommand):
    help = """
    DJPT command to print the worst performing items based on the
    vailable collectors
    """

    def handle(self, *args, **kwargs):
        self.report = WorstReport()
        datafile_path = get_datafile_path()
        reader = Reader(datafile_path)
        reader.read_all()
        self.report.render(self.stdout)
