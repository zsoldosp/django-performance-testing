from django.dispatch import Signal


result_collected = Signal(providing_args=('result', 'extra_context'))
