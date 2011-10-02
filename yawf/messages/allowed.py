# -*- coding: utf-8 -*-
from yawf import get_workflow_by_instance


def get_allowed_messages(sender, obj):
    workflow = get_workflow_by_instance(obj)

    check_result = dict((c, c(obj, sender)) for c in
            workflow.get_message_checkers_by_state(obj.state))

    for checkers, message in workflow.get_available_messages(obj.state):
        if any(check_result.get(i) for i in checkers):
            yield message


def get_message_specs(sender, obj):

    workflow = get_workflow_by_instance(obj)
    return [workflow.get_message_spec(mid)
                for mid in get_allowed_messages(sender, obj)]


def is_valid_message(obj, message_id):
    workflow = get_workflow_by_instance(obj)

    return workflow.is_valid_message(message_id, obj.state)
