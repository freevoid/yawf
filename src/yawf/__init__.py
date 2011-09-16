# -*- coding: utf-8 -*-
from operator import attrgetter

from yawf.exceptions import (
        WorkflowNotLoadedError,
        WorkflowAlreadyRegisteredError)
from yawf.config import WORKFLOW_TYPE_ATTR

_registry = {}
_by_rank = []


# function to use by workflow objects to register themselves
def register_workflow(workflow):
    pass # this is done in workflow constructor now


def _register_workflow(workflow):

    if workflow.id in _registry:
        raise WorkflowAlreadyRegisteredError(workflow.id, workflow)

    _registry[workflow.id] = workflow
    _by_rank.append(workflow)
    _by_rank.sort(key=attrgetter('rank'))


# external api
get_registered_workflows = lambda: _by_rank
get_workflow = _registry.get


def get_workflow_name_map():
    return dict((workflow.id, workflow.verbose_name) for workflow
            in _registry.itervalues())


def get_workflow_display_name(id):
    return get_workflow(id).verbose_name


def get_workflow_by_instance(obj):
    workflow_type = getattr(obj, WORKFLOW_TYPE_ATTR)
    workflow = get_workflow(workflow_type)
    if workflow is None:
        raise WorkflowNotLoadedError(workflow_type)
    return workflow


def autodiscover():
    # borrowed from admin.autodiscover
    from django.conf import settings
    from django.utils.importlib import import_module

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # Attempt to import the app's workflow module.
        _try_to_import(mod, app, 'workflow')
        _try_to_import(mod, app, 'workflows')


def _try_to_import(mod, app, module_name):

    global _registry

    import copy
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    try:
        before_import_registry = copy.copy(_registry)
        import_module('.'.join([app, module_name]))
    except:
        # Reset the model registry to the state before the last import as
        # this import will have to reoccur on the next request and this
        # could raise NotRegistered and AlreadyRegistered exceptions
        # (see #8245).
        _registry = before_import_registry

        # Decide whether to bubble up this error. If the app just
        # doesn't have an admin module, we can ignore the error
        # attempting to import it, otherwise we want it to bubble up.
        if module_has_submodule(mod, module_name):
            raise
