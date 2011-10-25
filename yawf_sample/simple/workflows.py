from django import forms

from yawf.base import WorkflowBase
from yawf.messages.common import message_spec_fabric, BasicStartMessage, MessageSpec
from yawf.messages.submessage import Submessage, RecursiveSubmessage

from yawf.actions import SideEffect
from yawf.handlers import SimpleStateTransition, Handler, ComplexStateTransition
from yawf.utils import make_common_updater
from .models import Window, WINDOW_OPEN_STATUS


class SimpleWorkflow(WorkflowBase):

    id = 'simple'
    verbose_name = 'Just a simple workflow'
    model_class = Window
    state_choices = WINDOW_OPEN_STATUS.choices
    state_attr_name = 'open_status'

simple_workflow = SimpleWorkflow()


@simple_workflow.register_message_by_form('click')
class ClickForm(forms.Form):

    pos_x = forms.IntegerField()
    pos_y = forms.IntegerField()


@simple_workflow.register_message
class ResizeMessage(MessageSpec):

    id = 'edit__resize'
    verb = 'Resize window'

    class Validator(forms.Form):

        width = forms.IntegerField(min_value=1)
        height = forms.IntegerField(min_value=1)

    @staticmethod
    def params_wrapper(params):
        return {'edit_fields': params}


simple_workflow.register_message(message_spec_fabric(id='minimize', verb='Minimize window'))
simple_workflow.register_message(message_spec_fabric(id='maximize'))
simple_workflow.register_message(message_spec_fabric(id='minimize_all'))
simple_workflow.register_message(BasicStartMessage)

@simple_workflow.register_handler
class Start(SimpleStateTransition):

    message_id = 'start_workflow'
    states_from = ['init']
    state_to = 'normal'

@simple_workflow.register_handler
class ToMinimized(SimpleStateTransition):

    message_id = 'minimize'
    states_from = ['normal', 'maximized']
    state_to = 'minimized'

@simple_workflow.register_handler
class ToMaximized(SimpleStateTransition):

    message_id = 'maximize'
    states_from = ['normal', 'minimized']
    state_to = 'maximized'

#NOTE: example of complex state transition
@simple_workflow.register_handler
class MinimizeAll(ComplexStateTransition):

    message_id = 'minimize_all'
    states_from = ['normal', 'maximized']

    def transition(self, obj, sender):
        yield (yield RecursiveSubmessage('minimize', sender))
        for child_window in obj.children.all():
            yield (yield Submessage(child_window, 'minimize', sender))

@simple_workflow.register_handler(states_from=['maximized', 'minimized'])
def to_normal(obj, sender):
    return 'normal'

@simple_workflow.register_handler
class Edit(Handler):

    message_group = 'edit'
    states_to = ['_']
    is_annotated = True

    def perform(self, obj, sender, edit_fields):
        return make_common_updater(edit_fields)


@simple_workflow.register_action
class SignalizeEdit(SideEffect):

    message_group = 'edit'

    def perform(self, **kwargs):
        return 'edit_effect'


@simple_workflow.register_action
class SignalizeResize(SideEffect):

    message_id = 'edit__resize'

    def perform(self, **kwargs):
        return 'resize_effect'

#simple_workflow._clean_deferred_chain()
