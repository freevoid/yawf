import logging
import collections

from yawf.permissions import BasePermissionChecker, OrChecker

logger = logging.getLogger(__name__)


class Handler(object):
    '''
    Basic class to express state transitions, both simple and extended.

    Handler object is a callable. It gets a workflow object, message sender
    and arbitrary keyword arguments (passed with message) and must return
    new state id based on this information (it can return None and message
    will be ignored).

    If handler returns a callable, then this callable applies as transaction
    on object (to change its extended state). The result of the latter
    callable represents affected instances. If callable returns generator,
    transition routine will coerce it to list to get those affected
    instances.

    Transitioning callable is not always must return generator or iterable.

    It can return None if nothing but the workflow object is affected.
    It can also return whatever it wants, but in this case one must avoid
    using the builtin mechanisms for message logging or make a custom
    signal handler for this purpose.
    '''
    message_id = None
    message_group = None
    states_from = None
    permission_checker = None
    defer = True
    replace_if_exists = False
    copy_before_call = False

    def __init__(self, message_id=None, states_from=None,
            message_group=None,
            permission_checker=None):

        if message_id is not None:
            self.message_id = message_id
        if message_group is not None:
            self.message_group = message_group
        if states_from is not None:
            self.states_from = states_from
        if permission_checker is not None:
            self.permission_checker = permission_checker

        message_group = self.message_group

        if message_group is not None:
            if isinstance(message_group, basestring):
                self.message_group = [message_group]
            else:
                assert isinstance(message_group, collections.Iterable)
        elif self.message_id is None:
            raise ValueError("message_id must be specified for handler")

        if self.permission_checker is not None:
            self._align_permission_checker()

        super(Handler, self).__init__()

    def _align_permission_checker(self):
        if not isinstance(self.permission_checker, collections.Iterable):
            if not isinstance(self.permission_checker, BasePermissionChecker):
                self.permission_checker = OrChecker(self.permission_checker,)
        else:
            self.permission_checker = OrChecker(*self.permission_checker)

        assert callable(self.permission_checker)

    def __call__(self, obj, sender, **kwargs):
        return self.perform(obj, sender, **kwargs)

    def perform(self, obj, sender, **kwargs):
        logger.warning("Message ignored (by default)")
        return None

    def set_performer(self, handle_func):
        self.perform = lambda obj, sender, **kwargs:\
            handle_func(obj, sender, **kwargs)


class SimpleStateTransition(Handler):

    state_to = None

    def __init__(self, *args, **kwargs):
        self.states_to = [self.state_to]
        self.is_annotated = True
        super(SimpleStateTransition, self).__init__(*args, **kwargs)

    def perform(self, obj, sender, **kwargs):
        return self.state_to


class ComplexStateTransition(Handler):

    def transition(self, obj, sender, **kwargs):
        raise NotImplementedError

    def perform(self, obj, sender, **kwargs):
        return lambda obj: self.transition(obj, sender, **kwargs)
