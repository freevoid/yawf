# -*- coding: utf-8 -*-
import logging

from yawf.config import STATE_TYPE_CONSTRAINT, REVISION_ATTR
from yawf.exceptions import IllegalStateError,\
         WrongHandlerResultError, PermissionDeniedError,\
         MessageIgnored
from yawf.signals import message_handled
from yawf import get_workflow_by_instance
from yawf.messages import Message, clean_message_data
from yawf.state_transition import transactional_transition

logger = logging.getLogger(__name__)



def dispatch(obj, sender, message_id, raw_params=None):
    return dispatch_message(obj, Message(sender, message_id, raw_params))


def dispatch_message(obj, message):
    logger.info(u"Backend got message from %s to %s: %s %s",
            message.sender, obj, message.id, message.raw_params)

    # can raise WorkflowNotLoadedError
    workflow = get_workflow_by_instance(obj)

    # validate data and filter out trash
    message = clean_message_data(workflow, obj, message)

    current_state = getattr(obj, workflow.state_attr_name)
    handler = workflow.get_handler(current_state, message.id)

    # check permission for a sender
    if not handler.permission_checker(obj, message.sender):
        raise PermissionDeniedError(obj, message)

    handler_result = apply(handler, (obj, message.sender), message.params)

    # if handler returns None - do nothing
    if handler_result is None:
        raise MessageIgnored(message.id, message.params)

    # if handler returns type appropriate for state (string) - change state
    if isinstance(handler_result, STATE_TYPE_CONSTRAINT):
        if workflow.is_valid_state(handler_result):
            def state_transition(clarified):
                setattr(clarified, workflow.state_attr_name, handler_result)
                clarified.save()
                return clarified
        else:
            raise IllegalStateError(handler_result)
    # if handler returns callable, perform it as single transaction
    elif callable(handler_result):
        state_transition = handler_result
    else:
        raise WrongHandlerResultError(handler_result)

    new_obj, transition_result, side_effect_result =\
        transactional_transition(workflow, obj, message, state_transition)

    new_revision = getattr(new_obj, REVISION_ATTR, None)

    message_handled.send(
            sender=workflow.id,
            message=message,
            instance=obj,
            transition_result=transition_result,
            new_revision=new_revision)

    return new_obj, side_effect_result
