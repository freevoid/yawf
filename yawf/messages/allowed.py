# -*- coding: utf-8 -*-
from operator import attrgetter

from yawf import get_workflow_by_instance


def get_allowed_messages(sender, obj, cache=None):
    workflow = get_workflow_by_instance(obj)

    if cache is None:
        cache = dict((c, c(obj, sender)) for c in
                workflow.get_message_checkers_by_state(obj.state))

    for checker, message in workflow.get_available_messages(obj.state):
        if checker(obj, sender, cache=cache):
            yield message


def get_allowed_messages_for_many(sender, objects):

    cache = {}

    for obj in objects:
        workflow = get_workflow_by_instance(obj)
        _update_cache(cache, workflow, obj, sender)

    allowed_map = {}
    for obj in objects:
        allowed_map[obj] = list(get_allowed_messages(sender, obj, cache=cache))

    return allowed_map


def get_message_specs_for_many(sender, objects):

    allowed_map = get_allowed_messages_for_many(sender, objects)

    for obj in objects:
        workflow = get_workflow_by_instance(obj)
        allowed_map[obj] = map(workflow.get_message_spec, allowed_map[obj])

    return allowed_map


def _update_cache(cache, workflow, obj, sender):

    for c in workflow.get_message_checkers_by_state(obj.state):
        if c not in cache:
            cache[c] = c(obj, sender)


def get_message_specs(sender, obj):

    workflow = get_workflow_by_instance(obj)
    return [workflow.get_message_spec(mid)
                for mid in get_allowed_messages(sender, obj)]


def is_valid_message(obj, message_id):
    workflow = get_workflow_by_instance(obj)

    return workflow.is_valid_message(message_id, obj.state)


class AllowedWrapper(object):

    def __init__(self, sender, obj, specs=None):
        self.sender = sender
        self.obj = obj
        self._specs = specs
        self._messages_lookup = None

    def _init_lookup(self):
        if self._specs is None:
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


def annotate_with_allowed_messages(sender, objects):

    allowed_map = get_message_specs_for_many(sender, objects)
    for obj, specs in allowed_map.iteritems():
        obj.allowed_messages = AllowedWrapper(sender, obj, specs=specs)
