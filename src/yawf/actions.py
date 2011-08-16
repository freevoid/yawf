'''
Action in yawf is a side-effect that can be performed after certain changes in
workflow.
'''

class SideEffectAction(object):

    message_id = None
    states_from = None
    states_to = None

    def __init__(self, message_id=None, states_from=None, states_to=None):

        if message_id is not None:
            self.message_id = message_id
        if states_to is not None:
            self.states_to = states_to
        if states_from is not None:
            self.states_from = states_from

    def perform(self, **kwargs):
        return kwargs

    def set_performer(self, performer):
        self.perform = lambda self, **kwargs: performer(**kwargs)

    def __call__(self, **kwargs):
        return self.perform(**kwargs)

    @property
    def name(self):
        return self.__class__.__name__
