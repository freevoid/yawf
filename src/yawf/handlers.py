import logging
import collections

from yawf.permissions import BasePermissionChecker, OrChecker

logger = logging.getLogger(__name__)


class Handler(object):

    message_id = None
    message_group = None
    states_from = None
    permission_checker = None
    defer = False

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
        elif message_id is None:
            raise ValueError("message_id must be specified for handler")

        if not isinstance(self.permission_checker, collections.Iterable):
            if not isinstance(self.permission_checker, BasePermissionChecker):
                self.permission_checker = OrChecker(self.permission_checker,)
        else:
            self.permission_checker = OrChecker(*self.permission_checker)

        assert callable(self.permission_checker)

        super(Handler, self).__init__()

    def __call__(self, obj, sender, **options):
        return self.handle(obj, sender, **options)

    def handle(self, obj, sender, **options):
        logger.warning("Message ignored (by default)")
        return None

    def set_handler(self, handle_func):
        self.handle = lambda self, **kwargs: handle_func(**kwargs)
