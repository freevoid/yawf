from django.template.response import TemplateResponse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.views.generic.edit import ProcessFormView
from django.views.generic.detail import SingleObjectMixin

from yawf import get_workflow
from yawf import dispatch
from yawf.exceptions import MessageValidationError
from yawf.graph import build_effects_graph, build_handlers_graph


class MessageViewMixin(object):

    message_id = None

    def get_message_id(self):

        dynamic_message_id = self.kwargs.get('message_id')
        return self.message_id\
            if dynamic_message_id is None else dynamic_message_id

    def get_sender(self, *args, **kwargs):

        return self.request.user


class YawfMessageView(MessageViewMixin, SingleObjectMixin, ProcessFormView):

    def post(self, request, *args, **kwargs):

        obj = self.get_object()
        msg_id = self.get_message_id()
        sender = self.get_sender()

        try:
            obj, handler_result, effect_result = dispatch.dispatch(obj, sender,
                    msg_id, self.request.POST)
        except MessageValidationError as e:
            return self.form_invalid(e.validator)
        else:
            return self.wrap_yawf_result(obj, handler_result, effect_result)

    def wrap_yawf_result(self, obj, handler_result, effect_result):
        return HttpResponseRedirect(self.get_success_url())


class HandlerViewMixin(MessageViewMixin):

    states_from = None
    permission_checker = None
    workflow_type = None

    @classmethod
    def as_view(cls, **initkwargs):
        view = super(HandlerViewMixin, cls).as_view(**initkwargs)

        workflow = get_workflow(cls.workflow_type)
        workflow.library.handler(
            message_id=view.get_message_id(),
            states_from=view.states_from,
            permission_checker=view.permission_checker)(view.perform)

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


def handlers_graph(request, workflow_id):
    return _graph_view(request, workflow_id, build_handlers_graph)


def effects_graph(request, workflow_id):
    return _graph_view(request, workflow_id, build_effects_graph)


def _graph_view(request, workflow_id, build_func):
    w = get_workflow(workflow_id)
    if w is None:
        raise Http404

    response = HttpResponse(mimetype='image/png')

    graph = build_func(w)
    graph.layout('dot')
    graph.draw(response, format='png')

    return response
