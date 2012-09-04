from django import forms

from yawf.creation import CreationAwareWorkflow
from yawf.messages.common import message_spec_fabric, BasicStartMessage, MessageSpec
from yawf.messages.submessage import Submessage, RecursiveSubmessage

from yawf.actions import SideEffect
from yawf.handlers import SimpleStateTransition, Handler, EditHandler, LoopHandler, StartWorkflowHandlerBase
from yawf.utils import make_common_updater
from yawf.annotation import annotate_handler

from yawf_sample.simple.models import Window, WINDOW_OPEN_STATUS

class MessageGroupsTestWorkflow(CreationAwareWorkflow):

    id = 'message_groups'
    verbose_name = 'Workflow to test message grouping'
    model_class = Window
    state_choices = WINDOW_OPEN_STATUS.choices
    state_attr_name = 'open_status'


workflow = MessageGroupsTestWorkflow()
register = workflow.library

register.message(BasicStartMessage)

@register.handler
class StartWorkflowHandler(StartWorkflowHandlerBase):
    state_to = WINDOW_OPEN_STATUS.NORMAL


class WindowEditHandler(EditHandler):

    message_group = 'edit'

register.handler(WindowEditHandler)


@register.message
class EditMessageSpec(MessageSpec):

    id = 'edit'

    class Validator(forms.ModelForm):
        class Meta:
            model = Window
            fields = ('title', 'width', 'height')


@register.message
class EditTitleMessageSpec(MessageSpec):

    id = 'edit__title'

    class Validator(forms.ModelForm):
        class Meta:
            model = Window
            fields = ('title',)


@register.message
class EditSizeMessageSpec(MessageSpec):

    id = 'edit__resize'

    class Validator(forms.ModelForm):
        class Meta:
            model = Window
            fields = ('width', 'height')


@register.message
class HoverMessageSpec(MessageSpec):

    id = 'hover'

    class Validator(forms.Form):

        pos_x = forms.IntegerField()
        pos_y = forms.IntegerField()


@register.handler
class HoverHandler(LoopHandler):

    message_id = 'hover'
    message_group = 'hover'
