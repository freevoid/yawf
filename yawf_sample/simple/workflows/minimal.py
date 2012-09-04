from yawf.base import WorkflowBase
from yawf.handlers import StartWorkflowHandlerBase
from yawf.messages.common import BasicStartMessage

from yawf_sample.simple.models import Window, WINDOW_OPEN_STATUS


class MinimalWorkflow(WorkflowBase):

    id = 'minimal'
    state_choices = WINDOW_OPEN_STATUS.choices
    model_class = Window

workflow = MinimalWorkflow()
register = workflow.library

register.message(BasicStartMessage)

class StartWorkflowHandler(StartWorkflowHandlerBase):
    state_to = WINDOW_OPEN_STATUS.NORMAL

register.handler(StartWorkflowHandler)
