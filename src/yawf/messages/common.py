from django.utils.translation import ugettext_lazy as _

from yawf.messages.spec import MessageSpec


class BasicCancelMessage(MessageSpec):

    id = 'cancel'
    verb = _('delete')
    rank = 1000


class BasicEditMessage(MessageSpec):

    id = 'edit'
    verb = _('change')
    rank = 900

    @staticmethod
    def params_wrapper(params):
        return {'edit_fields': params}


class BasicStartMessage(MessageSpec):

    id = 'start_workflow'
    verb = _('create')


class BasicPassedMessage(MessageSpec):

    id = 'passed'
    verb = _('mark passed')


class BasicCameMessage(MessageSpec):

    id = 'came'
    verb = _('mark came')
