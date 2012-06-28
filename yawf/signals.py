from django.dispatch import Signal

message_handled = Signal(
    providing_args=[
        'workflow',
        'message',
        'instance',
        'new_instance',
        'transition_result',
        'side_effect_result',
        'log_record',
    ])

transition_handled = Signal(
    providing_args=[
        'workflow',
        'message',
        'instance',
        'new_instance',
        'transition_result'
    ])
