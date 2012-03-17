'''
SideEffect in yawf is a side-effect action that can be performed
after certain changes in workflow.
'''
import collections


class SideEffect(object):

    message_id = None
    message_group = None
    states_from = None
    states_to = None
    is_transactional = False

    def __init__(self, message_id=None,
            states_from=None, states_to=None,
            message_group=None):

        if message_id is not None:
            self.message_id = message_id
        if message_group is not None:
            self.message_group = message_group
        if states_to is not None:
            self.states_to = states_to
        if states_from is not None:
            self.states_from = states_from

        message_group = self.message_group

        if message_group is not None:
            if isinstance(message_group, basestring):
                self.message_group = [message_group]
            else:
                assert isinstance(message_group, collections.Iterable)

        super(SideEffect, self).__init__()

    def perform(self, **kwargs):
        return kwargs

    def set_performer(self, performer):
        self.perform = lambda **kwargs: performer(**kwargs)

    def __call__(self, **kwargs):
        return self.perform(**kwargs)

    @property
    def name(self):
        return self.__class__.__name__


# for backward-compatibility
SideEffectAction = SideEffect
