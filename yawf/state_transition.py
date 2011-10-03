# -*- coding: utf-8 -*-
import logging
from types import GeneratorType

from django.db import transaction

from yawf.signals import transition_handled
from yawf.utils import select_for_update
from yawf.config import REVISION_ATTR, USE_SELECT_FOR_UPDATE
from yawf import get_workflow_by_instance
from yawf.exceptions import OldStateInconsistenceError,\
         ConcurrentRevisionUpdate

logger = logging.getLogger(__name__)


def transactional_transition(workflow, obj, message, state_transition,
        transactional_side_effect=True, extra_context=None):
    '''
    Function-dispatcher that allows to control the performing of
    side-effect actions.

    If transactional_side_effect is True, then side effect will be
    performed with selected for update object.

    Otherwise, it will be performed after handler commit.
    '''

    if transactional_side_effect:
        return _transactional_transition(workflow, obj, message,
                state_transition, extra_context=extra_context,
                transactional_side_effect=True)
    else:
        new_obj, transition_result, _ =  _transactional_transition(
                workflow, obj, message,
                state_transition,
                transactional_side_effect=False)
        side_effect_result = list(perform_side_effect(
                obj,
                new_obj,
                message=message,
                workflow=workflow,
                extra_context=extra_context))
        return new_obj, transition_result, side_effect_result


@transaction.commit_on_success
def _transactional_transition(workflow, obj, message, state_transition,
        transactional_side_effect=True, extra_context=None):
    old_revision = getattr(obj, REVISION_ATTR, None)
    old_state = getattr(obj, workflow.state_attr_name)
    obj_id = obj.id

    # We select for update object because since THIS point we cares
    # about serialization of access to our: we are going to change it's state
    if USE_SELECT_FOR_UPDATE:
        locked_obj = select_for_update(workflow.model_class.objects.filter(id=obj_id))[0]
    else:
        locked_obj = workflow.model_class.objects.filter(id=obj_id)[0]
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

    # all ok, perform db changes as transaction
    affected_objects = state_transition(locked_obj)

    # force generator evaluation, if state transition is generator function
    if isinstance(affected_objects, GeneratorType):
        affected_objects = list(affected_objects)

    new_revision = getattr(locked_obj, REVISION_ATTR, None)

    transition_handled.send(
            sender=workflow.id,
            workflow=workflow,
            message=message,
            instance=obj,
            new_instance=locked_obj,
            transition_result=affected_objects,
            new_revision=new_revision)

    if transactional_side_effect:
        # perform side effect action defined for transition
        side_effect_result = list(perform_side_effect(
                obj,
                locked_obj,
                message=message,
                workflow=workflow,
                extra_context=extra_context))
    else:
        side_effect_result = None

    new_state = getattr(locked_obj, workflow.state_attr_name)
    logger.info("Performed state transition of object %d: %s -> %s",
            obj_id, old_state, new_state)
    return locked_obj, affected_objects, side_effect_result


def perform_side_effect(old_obj, new_obj,
        message, workflow=None, extra_context=None):

    if workflow is None:
        workflow = get_workflow_by_instance(new_obj)

    old_state = getattr(old_obj, workflow.state_attr_name)
    new_state = getattr(new_obj, workflow.state_attr_name)

    effects = workflow.library.get_effects(
            old_state, new_state, message.id)

    if extra_context is None:
        extra_context = {}

    if effects:
        for effect in effects:
            yield effect(
                old_obj=old_obj,
                obj=new_obj,
                sender=message.sender,
                params=message.params,
                message_spec=message.spec,
                extra_context=extra_context,
            )
    else:
        logger.info(u"Effect undefined: object id %s, state %s -> %s",
                new_obj.id, old_state, new_state)
        return
