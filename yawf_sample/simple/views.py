# Create your views here.
from django import http

from yawf.views import YawfMessageView, HandlerViewMixin

from yawf_sample.simple.models import Window


class ResizeView(YawfMessageView):

    workflow_type = 'simple'
    model = Window
    message_id = 'edit__resize'

    def get_success_url(self):
        return '/'


class ToMaximizedView(HandlerViewMixin, YawfMessageView):

    workflow_type = 'simple'
    states_from = 'normal', 'minimized'

    def get_message_id(self):
        return 'maximize'

    def perform(self, obj, sender):
        return 'maximized'

    def wrap_yawf_result(self, obj, hr, er):
        return http.HttpResponse('OK')


window_resize = ResizeView.as_view()
window_maximize = ToMaximizedView.as_view()
