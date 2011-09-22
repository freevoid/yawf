# -*- coding: utf-8 -*-
from yawf import get_workflow_by_instance


def get_allowed_resources(sender, obj):

    workflow = get_workflow_by_instance(obj)

    check_result = dict((c, c(obj, sender)) for c in
            workflow.get_checkers_by_state(obj.state))

    for resource in workflow.get_available_resources(obj.state):
        if resource.permission_checker(obj, sender, cache=check_result):
            yield resource


def get_resource(obj, resource_id):
    workflow = get_workflow_by_instance(obj)

    return workflow.get_resource(obj.state, resource_id)
