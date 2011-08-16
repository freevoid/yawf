# -*- coding: utf-8 -*-
import logging

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
    old_state = obj.state
    obj_id = obj.id
    old_obj = obj
    obj = select_for_update(workflow.model_class.objects.filter(id=obj_id))[0]
    new_revision = getattr(obj, REVISION_ATTR, None)
    if old_revision is not None and new_revision != old_revision:
        raise ConcurrentRevisionUpdate(workflow.id, obj_id, obj.state)

    if obj.state != old_state:
        raise OldStateInconsistenceError(obj_id,
                old_state, obj.state)
    # all ok, perform db changes as transaction
    clarified = obj.get_clarified_instance() or obj

    # do db changes
    state_transition(clarified)

    # perform side effect action defined for transition
    side_effect_result = perform_side_effect(old_obj, obj,
            message=message,
            workflow=workflow)

    logger.info("Performed state transition of object %d: %s -> %s",
            obj_id, old_state, clarified.state)
    return clarified, side_effect_result


def perform_side_effect(old_obj, new_obj,
        message, workflow=None):

    if workflow is None:
        workflow = get_workflow_by_instance(new_obj.workflow_type)

    action = workflow.get_action(
            old_obj.state, new_obj.state, message.id)
    if callable(action):
        return action(
            old_obj=old_obj,
            obj=new_obj,
            sender=message.sender,
            params=message.params
        )
    else:
        logger.warning(u"Action undefined: object id %s, state %s -> %s",
                new_obj.id, old_obj.state, new_obj.state)
        return None
