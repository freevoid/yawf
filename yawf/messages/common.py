from django.utils.translation import ugettext_lazy as _

from yawf.messages.spec import MessageSpec


def message_spec_fabric(id, verb=None, rank=0, base_spec=MessageSpec, **attrs):
    # NOTE: reflect old behaviour when MessageSpec was registered as class
    # and this function was a class fabric.
    attrs.update({
        'rank': rank,
        'verb': verb,
        'id': id})
    return base_spec(**attrs)


BasicCancelMessage = MessageSpec(
    id='cancel',
    verb=_('cancel'),
    rank=1000,
)

BasicDeleteMessage = MessageSpec(
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


BasicStartMessage = MessageSpec(
    id='start_workflow',
    verb=_('create'),
)
