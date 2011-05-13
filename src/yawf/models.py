from django.db import models
from django.utils.translation import ugettext_lazy as _

from yawf import get_workflow_by_instance
from yawf.config import INITIAL_STATE


class WorkflowAwareModel(models.Model):

    class Meta:
        abstract = True

    state = models.CharField(default=INITIAL_STATE,
            max_length=32, db_index=True, editable=False,
            verbose_name=_('state'))

    @property
    def workflow(self):
        if not self._workflow:
            self._workflow = get_workflow_by_instance(self)
        return self._workflow

    def workflow_type_display(self):
        return self.workflow.verbose_name

    def state_display(self):
        return self.workflow.verbose_state_names.get(self.state) or self.state

    def get_clarified_instance(self):
        workflow = self.workflow

        if workflow.model_class is self.__class__:
            return self
        else:
            return workflow.model_class.objects.get(id=self.id)
