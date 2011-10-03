from django.db import transaction

from yawf.config import DEFAULT_START_MESSAGE, WORKFLOW_TYPE_ATTR
from yawf import get_workflow, get_workflow_by_instance
from yawf import dispatch
from yawf.exceptions import WorkflowNotLoadedError, CreateValidationError

@transaction.commit_on_success
def create(workflow_type, sender, raw_parameters):
    workflow = get_workflow(workflow_type)
    if workflow is None:
        raise WorkflowNotLoadedError(workflow_type)

    form = workflow.create_form_cls(raw_parameters)
    if form.is_valid():

        instance = workflow.instance_fabric(sender, form.cleaned_data)
        # Ensure that we will create, not update
        instance.id = None
        # Set workflow type
        setattr(instance, WORKFLOW_TYPE_ATTR, workflow_type)
        instance.save()

        workflow.post_create_hook(sender, form.cleaned_data, instance)

        return instance
    else:
        raise CreateValidationError(form.errors)


def start_workflow(obj, sender, start_message_params=None):
    if start_message_params is None:
        start_message_params = {}
    workflow = get_workflow_by_instance(obj)

    if isinstance(workflow.start_workflow, basestring):
        start_message_id = workflow.start_workflow
    elif callable(workflow.start_workflow):
        start_message_id  = workflow.start_workflow(obj, sender)
    else:
        start_message_id  = DEFAULT_START_MESSAGE

    return dispatch.dispatch(obj, sender, start_message_id,
                                                start_message_params)
