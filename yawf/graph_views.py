from django.http import Http404, HttpResponse

from yawf import get_workflow
from yawf.graph import build_effects_graph, build_handlers_graph


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
