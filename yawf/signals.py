from django.dispatch import Signal

message_handled = Signal(
    providing_args=[
        'workflow',
        'message',
        'instance',
        'new_instance',
        'new_revision',
        'transition_result'
    ])

transition_handled = Signal(
    providing_args=[
        'workflow',
        'message',
        'instance',
        'new_instance',
        'new_revision',
        'transition_result'
    ])