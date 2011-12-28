from django.utils.translation import ugettext_lazy as _

from yawf.messages.spec import MessageSpec, MessageSpecMeta


def message_spec_fabric(id, verb=None, rank=0, base_spec=MessageSpec, **attrs):
    attrs.update({
        'rank': rank,
        'verb': verb,
        'id': id})
    return MessageSpecMeta('Spec', (base_spec,), attrs)


BasicCancelMessage = message_spec_fabric(
    id='cancel',
    verb=_('cancel'),
    rank=1000,
)

BasicDeleteMessage = message_spec_fabric(
    id='delete',
    verb=_('delete'),
    rank=1001,
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
