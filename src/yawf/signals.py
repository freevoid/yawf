from django.dispatch import Signal

message_handled = Signal(providing_args=['message', 'instance', 'new_revision'])
