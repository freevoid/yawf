# -*- coding: utf-8 -*-

from django import forms
from django.template import loader as template_loader
from django.template import Context

from yawf.exceptions import WorkflowNotLoadedError, NoAvailableMessagesError
from yawf import get_workflow, get_workflow_by_instance
from yawf.messages.allowed import get_message_specs


def get_create_form_html(workflow_type, sender=None):
    workflow = get_workflow(workflow_type)
    if workflow is None:
        raise WorkflowNotLoadedError(workflow_type)

    form = workflow.create_form_cls()
    if not workflow.create_form_template:
        t = template_loader.select_template(
                ('gap/workflows/%s/create_form.html' % workflow_type,
                 'gap/workflows/create_form.html'))
    else:
        t = template_loader.get_template(workflow.create_form_template)

    context = Context({'form': form, 'workflow_type': workflow_type})
    return t.render(context)


def get_gap_as_html(obj, sender):
    workflow_type = obj.workflow_type
    allowed_messages = get_message_specs(sender, obj)

    t = template_loader.select_template(
            ('gap/workflows/%s/gap_%s.html' % (workflow_type, obj.state),
                'gap/workflows/%s/gap.html' % workflow_type,
                'gap/workflows/gap.html'))

    context = Context({'message_specs': allowed_messages, 'gap': obj})
    return t.render(context)


def get_gap_action_form_html(obj, sender):
    workflow_type = obj.workflow_type
    workflow = get_workflow_by_instance(obj)
    allowed_messages = get_message_specs(sender, obj)

    t = template_loader.select_template(
            ('gap/workflows/%s/gap_form_%s.html' % (workflow_type, obj.state),
                'gap/workflows/%s/gap_form.html' % workflow_type,
                'gap/workflows/gap_form.html'))

    if not allowed_messages:
        raise NoAvailableMessagesError(obj.id, sender)

    if callable(workflow.gapformcls_factory):
        form_cls = workflow.gapformcls_factory(allowed_messages)
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

    context = Context({'form': form, 'message_specs': allowed_messages, 'instance': obj})
    return t.render(context)
