def annotate_handler(states_to=('_',)):

    def decorator(handler):
        handler.states_to = states_to
        handler.is_annotated = True
        return handler

    return decorator
