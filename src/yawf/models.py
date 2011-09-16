from django.db import models
from django.utils.translation import ugettext_lazy as _

from yawf.config import INITIAL_STATE, REVISION_ENABLED, MESSAGE_LOG_ENABLED
from yawf.base_model import WorkflowAwareModelBase


class WorkflowAwareModel(WorkflowAwareModelBase):

    class Meta:
        abstract = True

    state = models.CharField(default=INITIAL_STATE,
            max_length=32, db_index=True, editable=False,
            verbose_name=_('state'))


if REVISION_ENABLED:
    from .revision import Revision, setup_handlers
    models.register_models('yawf', Revision)

    if MESSAGE_LOG_ENABLED:
        from .message_log import MessageLog
        models.register_models('yawf', MessageLog)

    setup_handlers()
