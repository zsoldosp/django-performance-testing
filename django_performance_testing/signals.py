from django.dispatch import Signal


results_collected = Signal(providing_args=('results', 'context'))

before_clearing_queries_log = Signal(providing_args=['queries'])

results_read = Signal(providing_args=('results', 'context'))
