from django.db import transaction

from yawf.config import DEFAULT_START_MESSAGE, WORKFLOW_TYPE_ATTR
from yawf import get_workflow, get_workflow_by_instance
from yawf import dispatch
from yawf.exceptions import WorkflowNotLoadedError, CreateValidationError
from yawf.base import WorkflowBase


class CreationAwareWorkflow(WorkflowBase):

    create_form_cls = None
    create_form_template = None

    def __init__(self, *args, **kwargs):
        super(CreationAwareWorkflow, self).__init__(*args, **kwargs)

    def get_create_form_cls(self):

        if self.create_form_cls is None:
            return form_for_model(self.model_class)
        elif isinstance(self.create_form_cls, basestring):
            return class_by_dotted_name(self.create_form_cls)
        else:
            return self.create_form_cls

    def instance_fabric(self, sender, cleaned_data):
        return self.model_class(**cleaned_data)

    def post_create_hook(self, sender, cleaned_data, instance):
        pass


@transaction.commit_on_success
def create(workflow_type, sender, raw_parameters):
    workflow = get_workflow(workflow_type)
    if workflow is None:
        raise WorkflowNotLoadedError(workflow_type)

    create_form_cls = workflow.get_create_form_cls()
    form = create_form_cls(raw_parameters)
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


def form_for_model(model_cls):
    from django.forms.models import modelform_factory
    return modelform_factory(model_cls)


class InvalidDottedNameError(ValueError):
    pass


def class_by_dotted_name(dotted_name):
    from django.utils import importlib
    try:
        # Trying to import the given backend, in case it's a dotted path
        mod_path, cls_name = dotted_name.rsplit('.', 1)
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
    except (AttributeError, ImportError, ValueError):
        raise InvalidDottedNameError("Could not find class '%s'" % dotted_name)
    else:
        return cls
