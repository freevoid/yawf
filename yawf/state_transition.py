# -*- coding: utf-8 -*-
import copy
import logging
from types import GeneratorType

from django.db import transaction

from yawf.signals import transition_handled
from yawf.utils import select_for_update
from yawf.config import REVISION_ATTR, USE_SELECT_FOR_UPDATE,\
        TRANSACTIONAL_SIDE_EFFECT
from yawf import get_workflow_by_instance
from yawf.exceptions import OldStateInconsistenceError,\
         ConcurrentRevisionUpdate
from yawf.messages.submessage import Submessage
from yawf.messages.transformation import TransformationResult

logger = logging.getLogger(__name__)


def transition(workflow, obj, message, state_transition,
        extra_context=None,
        transactional_side_effect=TRANSACTIONAL_SIDE_EFFECT,
        need_lock_object=USE_SELECT_FOR_UPDATE):
    '''
    Function-dispatcher that allows to control the performing of
    side-effect actions.

    :param transactional_side_effect:
        If `transactional_side_effect` is True, then side effect will be
        performed by :py:func:`transactional_transition`.

        Otherwise, it will be performed after handler commit.

    For other parameters and return values see
    :py:func:`transactional_transition`
    '''

    new_obj, transition_result, effect_result = transactional_transition(
            workflow, obj, message,
            state_transition,
            extra_context=extra_context,
            transactional_side_effect=transactional_side_effect,
            need_lock_object=need_lock_object)

    if not transactional_side_effect:
        effect_result = effect_result()

    return new_obj, transition_result, effect_result


@transaction.commit_on_success
def transactional_transition(workflow, obj, message, state_transition,
        extra_context=None,
        transactional_side_effect=True,
        need_lock_object=True):
    '''
    Performs an extended state transition for object `obj`. Uses
    `commit_on_success` to wrap itself in single transaction.

    :param workflow:
        :py:class:`yawf.base.WorkflowBase` instance, representing object's
        workflow.
    :param obj:
        Workflow aware object.
    :param message:
        :py:class:`yawf.messages.Message` instance.
    :param state_transition:
        callable that takes a single parameter: `obj` and must perform
        all state changes on it.

        Callable might return generator. In such case it will be iterated
        by special routine that filters out instances of
        :py:class:`yawf.messages.submessage.Submessage` class and dispatches
        them as messages within parent transaction context. Any other values
        yielded by generator will be accumulated and returned as a second
        element of result tuple.

        If callable returns something besides generator, the return value will
        be returned as a second element of result tuple.
    :param transactional_side_effect:
        Boolean flag. If `True`, then side effect actions will be performed
        just after state_transition func in single transaction. Otherwise,
        deferred side effect list will be returned (i.e. callable that
        will actually evaluate side effects and return a list of results)
    :return:
        Tuple with three values:
         * A new instance of workflow aware object (possibly changed after a
           state transition)
         * State transition result (list in the case of generator-based
           `state_transition` func, arbitrary object otherwise)
         * Side effect results (either list or a callable to evaluate that list)
    '''

    old_revision = getattr(obj, REVISION_ATTR, None)
    old_state = getattr(obj, workflow.state_attr_name)
    obj_id = obj.id

    # We select for update object because since THIS point we cares
    # about serialization of access to our: we are going to change it's state
    if need_lock_object:
        locked_obj = select_for_update(
                workflow.model_class.objects.filter(id=obj_id)).get()
        locked_revision = getattr(locked_obj, REVISION_ATTR, None)

        # Checking that revision wasn't updated while we worked with object
        # without locking
        if old_revision is not None and locked_revision != old_revision:
            raise ConcurrentRevisionUpdate(workflow.id, obj_id, old_state)

        # Additional checking of state consistency. Matters only if revision
        # check is disabled (getattr above returned None)
        locked_old_state = getattr(locked_obj, workflow.state_attr_name)
        if locked_old_state != old_state:
            raise OldStateInconsistenceError(obj_id,
                    old_state, locked_old_state)
    else:
        locked_obj = copy.copy(obj)

    # All ok, perform db changes as transaction
    transition_result = state_transition(locked_obj)

    new_obj = None

    # If action returned generator, evaluating it using special function
    if isinstance(transition_result, GeneratorType):
        handler_result, pending_calls, new_obj = _iterate_transition_result(
            transition_result, message, obj)
    else:
        handler_result = transition_result
        pending_calls = []

    if new_obj is None:
        new_obj = locked_obj

    # Sending signal
    transition_handled.send(
            sender=workflow.id,
            workflow=workflow,
            message=message,
            instance=obj,
            new_instance=new_obj,
            transition_result=handler_result)

    performed_effects, deferred_effects = perform_side_effect(
                                    obj,
                                    new_obj,
                                    message=message,
                                    workflow=workflow,
                                    handler_result=handler_result,
                                    extra_context=extra_context)


    # decide to evaluate side effect actions now or defer to caller
    if transactional_side_effect:
        side_effect_result = (performed_effects +
                                list(deferred_effects) +
                                map(apply, pending_calls))
    else:
        side_effect_result = lambda: (performed_effects +
                                list(deferred_effects) +
                                map(apply, pending_calls))

    new_state = getattr(new_obj, workflow.state_attr_name)
    logger.info("Performed state transition of object %d: %s -> %s",
            obj_id, old_state, new_state)
    return new_obj, handler_result, side_effect_result


def perform_side_effect(old_obj, new_obj,
        message, workflow=None, extra_context=None, handler_result=None):

    if workflow is None:
        workflow = get_workflow_by_instance(new_obj)

    old_state = getattr(old_obj, workflow.state_attr_name)
    new_state = getattr(new_obj, workflow.state_attr_name)

    (transactional_effects,
            deferrable_effects) = workflow.library\
                                        .get_effects_for_transition(
                                            old_state, new_state, message.id)

    if not transactional_effects and not deferrable_effects:
        logger.info(u"Effect undefined: object id %s, state %s -> %s",
                new_obj.id, old_state, new_state)
        return [], []

    if extra_context is None:
        extra_context = {}

    effect_kwargs = dict(
        old_obj=old_obj,
        obj=new_obj,
        sender=message.sender,
        params=message.params,
        message_spec=message.spec,
        extra_context=extra_context,
        handler_result=handler_result,
    )

    if transactional_effects:
        performed = [effect(**effect_kwargs) for effect in transactional_effects]
    else:
        performed = []
    if deferrable_effects:
        deferred = (effect(**effect_kwargs) for effect in deferrable_effects)
    else:
        deferred = []
    return performed, deferred


def _iterate_transition_result(transition_result, message, obj):

    pending_calls = []
    handler_result = []
    new_obj = None

    try:
        yielded_value = transition_result.next()
    except StopIteration:
        return handler_result, pending_calls, new_obj

    while True:
        to_send = None

        if isinstance(yielded_value, Submessage):
            sub_obj, _sub_result, side_effects_performer =\
                                        yielded_value.dispatch(
                                            parent_obj=obj,
                                            parent_message=message)
            pending_calls.append(side_effects_performer)
            to_send = sub_obj
        elif isinstance(yielded_value, TransformationResult):
            new_obj = yielded_value.new_obj
        else:
            handler_result.append(yielded_value)

        try:
            yielded_value = transition_result.send(to_send)
        except StopIteration:
            break

    return handler_result, pending_calls, new_obj
