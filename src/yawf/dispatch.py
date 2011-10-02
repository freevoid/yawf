# -*- coding: utf-8 -*-
import logging
from itertools import ifilter

from yawf.config import STATE_TYPE_CONSTRAINT, REVISION_ATTR,\
         TRANSACTIONAL_SIDE_EFFECT
from yawf.exceptions import IllegalStateError,\
         WrongHandlerResultError, PermissionDeniedError,\
         MessageIgnored
from yawf.signals import message_handled
from yawf import get_workflow_by_instance
from yawf.messages import Message, clean_message_data
from yawf.state_transition import transactional_transition

logger = logging.getLogger(__name__)



def dispatch(obj, sender, message_id, raw_params=None, extra_context=None):
    return dispatch_message(
            obj,
            Message(sender, message_id, raw_params),
            extra_context=extra_context)


def dispatch_message(obj, message, extra_context=None):
    logger.info(u"Backend got message from %s to %s: %s %s",
            message.sender, obj, message.id, message.raw_params)

    # can raise WorkflowNotLoadedError
    workflow = get_workflow_by_instance(obj)

    # validate data and filter out trash
    message = clean_message_data(workflow, obj, message)

    current_state = getattr(obj, workflow.state_attr_name)
    handlers = workflow.library.get_handlers(current_state, message.id)

    # check permission for a sender
    permitted_handlers = ifilter(
        lambda handler: handler.permission_checker(obj, message.sender),
        handlers)

    try:
        # NOTE: we will get permitted handler that was registered *first*,
        # if there are more than one handler for that state,message
        handler = permitted_handlers.next()
    except StopIteration:
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

    new_obj, transition_result, side_effect_results =\
        transactional_transition(
            workflow, obj, message, state_transition,
            extra_context=extra_context,
            transactional_side_effect=TRANSACTIONAL_SIDE_EFFECT)

    new_revision = getattr(new_obj, REVISION_ATTR, None)

    # TODO: send_robust + logging?
    message_handled.send(
            sender=workflow.id,
            workflow=workflow,
            message=message,
            instance=obj,
            new_instance=new_obj,
            transition_result=transition_result,
            new_revision=new_revision)

    return new_obj, side_effect_results
