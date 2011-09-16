# -*- coding: utf-8 -*-
import logging
from types import GeneratorType

from django.db import transaction

from yawf.utils import select_for_update
from yawf.config import REVISION_ATTR
from yawf import get_workflow_by_instance
from yawf.exceptions import OldStateInconsistenceError,\
         ConcurrentRevisionUpdate

logger = logging.getLogger(__name__)


@transaction.commit_on_success
def transactional_transition(workflow, obj, message, state_transition):
    old_revision = getattr(obj, REVISION_ATTR, None)
    old_state = getattr(obj, workflow.state_attr_name)
    obj_id = obj.id
    old_obj = obj

    # We select for update object because since THIS point we cares
    # about serialization of access to our: we are going to change it's state
    locked_obj = select_for_update(workflow.model_class.objects.filter(id=obj_id))[0]
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

    # perform side effect action defined for transition
    side_effect_result = perform_side_effect(old_obj, locked_obj,
            message=message,
            workflow=workflow)

    logger.info("Performed state transition of object %d: %s -> %s",
            obj_id, old_state, locked_obj.state)
    return locked_obj, affected_objects, side_effect_result


def perform_side_effect(old_obj, new_obj,
        message, workflow=None):

    if workflow is None:
        workflow = get_workflow_by_instance(new_obj)

    old_state = getattr(old_obj, workflow.state_attr_name)
    new_state = getattr(new_obj, workflow.state_attr_name)

    action = workflow.get_action(
            old_state, new_state, message.id)

    if callable(action):
        return action(
            old_obj=old_obj,
            obj=new_obj,
            sender=message.sender,
            params=message.params
        )
    else:
        logger.warning(u"Action undefined: object id %s, state %s -> %s",
                new_obj.id, old_state, new_state)
        return None
