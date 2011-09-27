from django.db import models
from django.utils.translation import ugettext_lazy as _

from yawf.config import INITIAL_STATE
from yawf.base_model import WorkflowAwareModelBase


class WorkflowAwareModel(WorkflowAwareModelBase):

    class Meta:
        abstract = True

    state = models.CharField(default=INITIAL_STATE,
            max_length=32, db_index=True, editable=False,
            verbose_name=_('state'))
