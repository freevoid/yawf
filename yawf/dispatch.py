# -*- coding: utf-8 -*-
import logging
import copy
from itertools import ifilter

from django.utils.encoding import smart_unicode

from yawf.message_log.models import log_message

from yawf.config import STATE_TYPE_CONSTRAINT,\
         TRANSACTIONAL_SIDE_EFFECT, USE_SELECT_FOR_UPDATE, MESSAGE_LOG_ENABLED
from yawf.exceptions import IllegalStateError,\
         WrongHandlerResultError, PermissionDeniedError,\
         MessageIgnored
from yawf.signals import message_handled
from yawf import get_workflow_by_instance
from yawf.messages import Message
from yawf.state_transition import transition, transactional_transition
from yawf.revision import default_revision_manager

logger = logging.getLogger(__name__)


class Dispatcher(object):
    '''
    Class-style dispatching.

    One can use Dispatcher instead of dispatch if it seems more natural.

    Example:

    >>> d = Dispatcher(obj, user, extra_context={'request': request})
    >>> new_obj, handler_result, effect_result = d.edit(foo='bar')

    So object-recipient and sender are passed to the dispatcher once and
    message passing is done by calling methods on dispatcher object.
    '''
    def __init__(self, obj, sender, **options):
        self.obj = obj
        self.sender = sender
        self.options = options
        super(Dispatcher, self).__init__()

    def __getattribute__(self, name):
        message_id = name
        return lambda **raw_params:\
            dispatch(self.obj, self.sender, message_id,
                    raw_params,
                    **self.options)



def dispatch(obj, sender, message_id, raw_params=None,
             **dispatch_options):
    '''
    High-level shortcut function to send a message to workflow-enabled object.

    See :py:func:`dispatch_message` for detailed information.
    '''
    message = Message(sender, message_id, raw_params)
    return dispatch_message(obj, message, **dispatch_options)


def dispatch_no_clean(obj, sender, message_id, params=None,
                      **dispatch_options):
    message = Message(sender, message_id, clean_params=params)
    return dispatch_message(obj, message, **dispatch_options)


def dispatch_message(obj, message,
                     extra_context=None,
                     transactional_side_effect=TRANSACTIONAL_SIDE_EFFECT,
                     need_lock_object=USE_SELECT_FOR_UPDATE,
                     defer_side_effect=False,
                     revision_manager=None):
    '''
    Gets an object and message and performs all actions specified by
    object's workflow.

    :param obj:
        Object that receives message. Must be an instance of
        :py:class:`yawf.base_model.WorkflowAwareModelBase`
    :param message:
        :py:class:`yawf.messages.Message` instance that incapsulates message sender and parameters

    :return:
        Tuple of three values:
         * new object instance (after state transition)
         * transition result (returned by handler object)
         * side effects results
    '''
    logger.debug(u"Backend got message from %s to %s: %s %s",
            smart_unicode(message.sender), smart_unicode(obj),
            message.id, smart_unicode(message.raw_params))

    # can raise WorkflowNotLoadedError
    workflow = get_workflow_by_instance(obj)

    # validate data and filter out trash
    message.clean(workflow, obj)

    # dehydrate message params for serializing
    message.dehydrate_params(workflow, obj)

    # find a transition handler, can raise handler-related errors
    handler = get_handler(workflow, message, obj)

    # fetch a transition, can raise app-specific handler errors
    handler_result = apply(handler, (obj, message.sender), message.params)

    # if handler returns None - do nothing
    if handler_result is None:
        raise MessageIgnored(message)

    # if handler returns type appropriate for state (string) - change state
    if isinstance(handler_result, STATE_TYPE_CONSTRAINT):
        if workflow.is_valid_state(handler_result):
            def state_transition(obj):
                setattr(obj, workflow.state_attr_name, handler_result)
                obj.save()
                return obj
        else:
            raise IllegalStateError(handler_result)

    # if handler returns callable, perform it as single transaction
    elif callable(handler_result):
        state_transition = handler_result
    else:
        raise WrongHandlerResultError(handler_result)

    if defer_side_effect:
        transition_ = transactional_transition
        transactional_side_effect = False
    else:
        transition_ = transition

    if revision_manager is None:
        revision_manager = default_revision_manager

    with revision_manager() as m:
        new_obj, transition_result, side_effect_result =\
            transition_(
                workflow, obj, message, state_transition,
                extra_context=extra_context,
                transactional_side_effect=transactional_side_effect,
                need_lock_object=need_lock_object)

        if MESSAGE_LOG_ENABLED:
            log_record = log_message(
                sender=workflow.id,
                workflow=workflow,
                message=message,
                instance=obj,
                new_instance=new_obj,
                transition_result=transition_result)

            m.bind_revision(log_record)
        else:
            log_record = None

    # TODO: send_robust + logging?
    message_handled.send(
            sender=workflow.id,
            workflow=workflow,
            message=message,
            instance=obj,
            new_instance=new_obj,
            transition_result=transition_result,
            side_effect_result=side_effect_result,
            log_record=log_record)

    return new_obj, transition_result, side_effect_result


def get_handler(workflow, message, obj):

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
    else:
        if handler.copy_before_call:
            handler = copy.deepcopy(handler)
        return handler
