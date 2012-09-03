import logging
import collections

from yawf.permissions import BasePermissionChecker, OrChecker
from yawf.config import INITIAL_STATE

logger = logging.getLogger(__name__)

__all__ = ['Handler', 'SimpleStateTransition', 'ComplexStateTransition',
        'EditHandler', 'SerializibleHandlerResult']


class Handler(object):
    '''
    Basic class to express state transitions, both simple and extended.

    Handler object is a callable. It gets a workflow object, message sender
    and arbitrary keyword arguments (passed with message) and must return
    new state id based on this information (it can return None and message
    will be ignored).

    If handler returns a callable, then this callable applies as transaction
    on object (to change its extended state). The result of the latter
    callable represents a transition result. If callable returns generator,
    transition routine will iterate over it, collecting the yielded values.
    For more information about state transition, see
    :py:mod:`yawf.state_transition` module.

    Transitioning callable can actually return anything besides generator.
    That is totally an application designer business.
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


class EditHandler(ComplexStateTransition):

    field_names = None

    def post_hook(self, obj):
        return

    def transition(self, obj, sender, **kwargs):

        # to ensure that we will update, not insert new
        kwargs.pop('id', None)
        kwargs.pop('pk', None)

        field_names = self.field_names
        if field_names:
            for field_name in field_names:
                value = kwargs.get(field_name, '__missing')
                if value != '__missing':
                    setattr(obj, field_name, value)
        else:
            for field_name in (f.name for f in obj._meta.fields):
                value = kwargs.get(field_name, '__missing')
                if value != '__missing':
                    setattr(obj, field_name, value)

            for field_name in (f.name for f in obj._meta.many_to_many):
                value = kwargs.get(field_name)
                if value is not None:
                    setattr(obj, field_name, value)

        obj.save()

        return self.post_hook(obj)


class LoopHandler(Handler):

    def perform(self, obj, sender, **kwargs):
        return getattr(obj, obj.workflow.state_attr_name)


class StartWorkflowHandlerBase(SimpleStateTransition):

    message_id = 'start_workflow'
    states_from = [INITIAL_STATE]


class SerializibleHandlerResult(object):

    type = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super(SerializibleHandlerResult, self).__init__()

    def get_serializible_value(self):
        return {
            'type': self.type,
            'result': self.kwargs,
        }
