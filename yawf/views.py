from django.template.response import TemplateResponse
from django.http import Http404, HttpResponseRedirect
from django.views.generic.edit import ProcessFormView
from django.views.generic.detail import SingleObjectMixin

from yawf import get_workflow
from yawf import dispatch
from yawf.exceptions import MessageValidationError


class MessageViewMixin(object):

    message_id = None

    def get_message_id(self):

        dynamic_message_id = self.kwargs.get('message_id')
        return self.message_id\
            if dynamic_message_id is None else dynamic_message_id

    def get_sender(self, *args, **kwargs):

        return self.request.user


class YawfMessageView(MessageViewMixin, SingleObjectMixin, ProcessFormView):

    @property
    def model(self):
        workflow = get_workflow(self.workflow_type)
        if hasattr(workflow, 'model_class'):
            return workflow.model_class

    def post(self, request, *args, **kwargs):

        obj = self.get_object()
        if hasattr(obj, 'get_clarified_instance'):
            obj = obj.get_clarified_instance()

        self.object = obj
        msg_id = self.get_message_id()
        sender = self.get_sender()

        try:
            obj, handler_result, effect_result = dispatch.dispatch(obj, sender,
                    msg_id, self.request.POST)
            self.object = obj
        except BaseException as e:
            return self.process_exception(obj, sender, msg_id, e)
        else:
            return self.wrap_yawf_result(obj, handler_result, effect_result)

    def wrap_yawf_result(self, obj, handler_result, effect_result):
        return HttpResponseRedirect(self.get_success_url())

    def process_exception(self, obj, sender, msg_id, exc):
        if isinstance(exc, MessageValidationError):
            return self.form_invalid(exc.validator)
        else:
            raise


class HandlerViewMixin(MessageViewMixin):

    states_from = None
    permission_checker = None
    workflow_type = None

    @classmethod
    def as_view(cls, **initkwargs):
        view = super(HandlerViewMixin, cls).as_view(**initkwargs)

        instance = cls(**initkwargs)
        workflow = get_workflow(cls.workflow_type)
        workflow.library.handler(
            message_id=instance.get_message_id(),
            states_from=instance.states_from,
            permission_checker=instance.permission_checker)(instance.perform)

        return view

    def perform(self, obj, sender, **kwargs):
        return lambda obj: self.transition(obj, sender, **kwargs)


# === Helper views for development/introspection

def describe_workflow(request, workflow_id):
    w = get_workflow(workflow_id)
    if w is None:
        raise Http404
    return TemplateResponse(request, 'yawf/describe_workflow.html',
            {'workflow': w})
