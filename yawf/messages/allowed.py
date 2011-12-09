# -*- coding: utf-8 -*-
from operator import attrgetter

from yawf import get_workflow_by_instance


def get_allowed_messages(sender, obj):
    workflow = get_workflow_by_instance(obj)

    check_result = dict((c, c(obj, sender)) for c in
            workflow.get_message_checkers_by_state(obj.state))

    for checker, message in workflow.get_available_messages(obj.state):
        if checker(obj, sender, cache=check_result):
            yield message


def get_message_specs(sender, obj):

    workflow = get_workflow_by_instance(obj)
    return [workflow.get_message_spec(mid)
                for mid in get_allowed_messages(sender, obj)]


def is_valid_message(obj, message_id):
    workflow = get_workflow_by_instance(obj)

    return workflow.is_valid_message(message_id, obj.state)


class AllowedWrapper(object):

    def __init__(self, sender, obj):
        self.sender = sender
        self.obj = obj
        self._messages_lookup = None

    def _init_lookup(self):
        self._specs = get_message_specs(self.sender, self.obj)
        self._messages_lookup = dict(
            (message.id, message)
            for message in self._specs
        )

    def __getitem__(self, message_id):
        if self._messages_lookup is None:
            self._init_lookup()

        return self._messages_lookup.get(message_id)

    def __iter__(self):
        return sorted(self._specs, key_func=attrgetter('rank'))
