from django.utils.translation import ugettext_lazy as _

from yawf.messages.spec import MessageSpec


def message_spec_fabric(id, verb=None, rank=0, **attrs):
    return type('Spec', (MessageSpec,), locals())


BasicCancelMessage = message_spec_fabric(
    id='cancel',
    verb=_('delete'),
    rank=1000,
)


class BasicEditMessage(MessageSpec):

    id = 'edit'
    verb = _('change')
    rank = 900

    @staticmethod
    def params_wrapper(params):
        return {'edit_fields': params}


BasicStartMessage = message_spec_fabric(
    id='start_workflow',
    verb=_('create'),
)


BasicPassedMessage = message_spec_fabric(
    id='passed',
    verb=_('mark passed'),
)


BasicCameMessage = message_spec_fabric(
    id='came',
    verb=_('mark came'),
)
