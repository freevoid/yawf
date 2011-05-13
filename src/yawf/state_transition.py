# -*- coding: utf-8 -*-
import logging

from django.db import transaction

from yawf.utils import select_for_update
from yamf.config import REVISION_ATTR
from yawf.exceptions import OldStateInconsistenceError,\
         ConcurrentRevisionUpdate

logger = logging.getLogger(__name__)


@transaction.commit_on_success
def perform_transition(workflow, obj_id, old_state, new_state, old_revision):
    obj = select_for_update(workflow.model_class.objects.filter(id=obj_id))[0]
    new_revision = getattr(obj, REVISION_ATTR, None)
    if old_revision is not None and new_revision != old_revision:
        raise ConcurrentRevisionUpdate(workflow.id, obj_id, obj.state)
    if obj.state != old_state:
        raise OldStateInconsistenceError(obj_id, old_state, obj.state)

    obj = obj.get_clarified_instance() or obj
    obj.state = new_state
    obj.save()
    logger.info("Performed state transition of object %d: %s -> %s",
            obj_id, old_state, new_state)
    return obj


@transaction.commit_manually
def perform_extended_transition(workflow, obj_id, old_state, fun, old_revision):
    try:
        obj = select_for_update(workflow.model_class.objects.filter(id=obj_id))[0]
        new_revision = getattr(obj, REVISION_ATTR, None)
        if old_revision is not None and new_revision != old_revision:
            raise ConcurrentRevisionUpdate(workflow.id, obj_id, obj.state)

        if obj.state != old_state:
            raise OldStateInconsistenceError(obj_id,
                    old_state, obj.state)
        # all ok, perform db changes as transaction
        clarified = obj.get_clarified_instance() or obj
        fun(clarified)
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()
        logger.info("Performed state transition of object %d: %s -> %s",
                obj_id, old_state, clarified.state)
        return clarified
