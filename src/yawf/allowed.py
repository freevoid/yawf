# -*- coding: utf-8 -*-
from yawf import get_workflow_by_instance


def get_allowed(sender, obj):
    workflow = get_workflow_by_instance(obj)

    check_result = dict((c, c(obj, sender)) for c in
            workflow.get_checkers_by_state(obj.state))

    messages = []
    for checkers, message in workflow.get_available_messages(obj.state):
        if any(check_result.get(i) for i in checkers):
            spec = workflow.get_message_spec(message)
            messages.append({'id': spec.id, 'title': spec.verb, 'rank': spec.rank})

    resources = []
    for resource in workflow.get_available_resources(obj.state):
        if any(check_result.get(i) for i in resource.checkers):
            resources.append(
                {'id': resource.id, 'description': resource.description})

    return {'allowed_messages': messages,
            'allowed_resources': resources}
