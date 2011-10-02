from django import forms

from yawf.base import WorkflowBase
from yawf.messages.common import message_spec_fabric, BasicStartMessage

from yawf.handlers import SimpleStateTransition
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


simple_workflow.register_message(message_spec_fabric(id='minimize', verb='Minimize window'))
simple_workflow.register_message(message_spec_fabric(id='maximize'))
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

@simple_workflow.register_handler
class ToNormal(SimpleStateTransition):

    message_id = 'to_normal'
    states_from = ['maximized', 'minimized']
    state_to = 'normal'
