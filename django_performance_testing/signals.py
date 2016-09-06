from django.dispatch import Signal


result_collected = Signal(providing_args=('result', 'context'))

before_clearing_queries_log = Signal(providing_args=['queries'])
