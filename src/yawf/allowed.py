# -*- coding: utf-8 -*-
from yawf import get_workflow_by_instance


def get_allowed(sender, obj):
    workflow = get_workflow_by_instance(obj)

    check_result = dict(
        (c, c(obj, sender))
        for c in workflow.get_checkers_by_state(obj.state))

    messages = []
    for checker, message in workflow.get_available_messages(obj.state):
        if checker(obj, sender, cache=check_result):
            spec = workflow.get_message_spec(message)
            messages.append({'id': spec.id, 'title': unicode(spec), 'rank': spec.rank})

    resources = []
    for resource in workflow.get_available_resources(obj.state):
        if resource.permission_checker(obj, sender, cache=check_result):
            resources.append(
                {
                    'id': resource.id,
                    'description': resource.description,
                    'slug': resource.slug,
                })

    return {'allowed_messages': messages,
            'allowed_resources': resources}
