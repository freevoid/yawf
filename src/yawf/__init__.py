# -*- coding: utf-8 -*-
from operator import attrgetter

from yawf.exceptions import WorkflowNotLoadedError
from yawf import config

_registered_workflows = {}
_by_rank = []

WORKFLOW_TYPE_ATTR = config.CONFIG['WORKFLOW_TYPE_ATTR']


# function to use by workflow callback modules to register themselves
def register_workflow(workflow):
    _registered_workflows[workflow.id] = workflow
    _by_rank.append(workflow)
    _by_rank.sort(key=attrgetter('rank'))

# external api
get_registered_workflows = lambda: _by_rank
get_workflow = _registered_workflows.get


def get_workflow_name_map():
    return dict((workflow.id, workflow.verbose_name) for workflow
            in _registered_workflows.itervalues())


def get_workflow_display_name(id):
    return get_workflow(id).verbose_name


def get_workflow_by_instance(obj):
    workflow_type = getattr(obj, WORKFLOW_TYPE_ATTR)
    workflow = get_workflow(workflow_type)
    if workflow is None:
        raise WorkflowNotLoadedError(workflow_type)
    return workflow
