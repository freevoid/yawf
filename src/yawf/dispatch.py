# -*- coding: utf-8 -*-
import logging

from yawf.config import STATE_TYPE_CONSTRAINT
from yawf.exceptions import IllegalStateError,\
         WrongHandlerResultError, PermissionDeniedError,\
         MessageIgnored
from yawf import get_workflow_by_instance
from yawf.signals import message_handled
from yawf.messages import Message, clean_message_data
from yawf.state_transition import perform_transition,\
         perform_extended_transition

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

    permission_checker, handler = workflow.get_handler(obj.state,
                                                                message.id)

    # check permission for a sender
    if not permission_checker(obj, message.sender):
        raise PermissionDeniedError(obj, message)

    handler_result = apply(handler, (obj, message.sender), message.params)

    # if handler returns None - do nothing
    if handler_result is None:
        raise MessageIgnored(message.id, message.params)

    # if handler returns type appropriate for state (string) - change state
    if isinstance(handler_result, STATE_TYPE_CONSTRAINT):
        if workflow.is_valid_state(handler_result):
            old_state = obj.state
            new_obj = perform_transition(
                    workflow, obj.id, old_state, handler_result)
        else:
            raise IllegalStateError(handler_result)
    # if handler returns callable, perform it as single transaction
    elif callable(handler_result):
        new_obj = perform_extended_transition(
            workflow, obj.id, obj.state, handler_result)
    else:
        raise WrongHandlerResultError(handler_result)


    message_handled.send(sender=workflow.id,
            message=message,
            instance=obj,
            new_revision=new_obj.revision)

    # perform side effect action defined for transition
    perform_side_effect(obj, new_obj,
            message=message,
            workflow=workflow)
    return new_obj


def perform_side_effect(old_obj, new_obj,
        message, workflow=None):

    if workflow is None:
        workflow = get_workflow_by_instance(new_obj.workflow_type)

    action = workflow.get_action(
            old_obj.state, new_obj.state, message.id)
    if callable(action):
        return action(old_obj, new_obj, message.sender,
                                                    **message.params)
    else:
        logger.warning(u"Action undefined: object id %s, state %s -> %s",
                new_obj.id, old_obj.state, new_obj.state)
        return None
