# -*- coding: utf-8 -*-

from django import forms
from django.template import loader as template_loader
from django.template import Context

from yawf import get_workflow, get_workflow_by_instance
from yawf.exceptions import WorkflowNotLoadedError, NoAvailableMessagesError
from yawf.messages.allowed import get_allowed


def get_create_form_html(workflow_type, sender=None):
    workflow = get_workflow(workflow_type)
    if workflow is None:
        raise WorkflowNotLoadedError(workflow_type)

    form = workflow.create_form_cls()
    if not workflow.create_form_template:
        t = template_loader.select_template(
                ('workflows/%s/create_form.html' % workflow_type,
                 'workflows/create_form.html'))
    else:
        t = template_loader.get_template(workflow.create_form_template)

    context = Context({'form': form, 'workflow_type': workflow_type})
    return t.render(context)


def get_object_as_html(obj, sender):
    workflow_type = obj.workflow_type
    allowed_context = get_allowed(sender, obj)

    t = template_loader.select_template(
            ('workflows/%s/object_%s.html' % (workflow_type, obj.state),
                'workflows/%s/object.html' % workflow_type,
                'workflows/object.html'))

    dict_context = {'object': obj}
    dict_context.update(allowed_context)
    context = Context(dict_context)
    return t.render(context)


def get_action_form_html(obj, sender):
    workflow_type = obj.workflow_type
    workflow = get_workflow_by_instance(obj)
    allowed_context = get_allowed(sender, obj)

    t = template_loader.select_template(
            ('workflows/%s/form_%s.html' % (workflow_type, obj.state),
                'workflows/%s/form.html' % workflow_type,
                'workflows/form.html'))

    allowed_messages = allowed_context['allowed_messages']
    if not allowed_messages:
        raise NoAvailableMessagesError(obj.id, sender)

    if callable(workflow.formcls_factory):
        form_cls = workflow.formcls_factory(allowed_messages)
        form = form_cls(instance=obj)
    else:
        # get all form subclasses from message validators, throw away duplicates
        bases = tuple(set(ms.validator_cls for ms in allowed_messages
                            if issubclass(ms.validator_cls, forms.BaseForm)))
        if bases:
            # join them all in one mixin class
            mixin_form_cls = type('WorkflowObjectMixinForm', bases, {})
            # instantiate it and put instance as argument (requires ModelForm subclass to be in bases)
            if issubclass(mixin_form_cls, forms.ModelForm):
                form = mixin_form_cls(instance=obj)
            else:
                form = mixin_form_cls(initial=obj.__dict__)
        else:
            form = forms.Form()

    dict_context = {'form': form, 'instance': obj}
    dict_context.update(allowed_context)
    context = Context(dict_context)
    return t.render(context)
