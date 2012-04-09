from django.utils.encoding import force_unicode

from yawf import get_workflow_by_instance


class WorkflowAwareModelBase(object):

    _workflow = None

    @property
    def workflow(self):
        if not self._workflow:
            self._workflow = get_workflow_by_instance(self)
        return self._workflow

    def workflow_type_display(self):
        return self.workflow.verbose_name

    def state_display(self):
        return force_unicode(self.workflow.verbose_state_names.get(self.state)) or self.state

    def get_clarified_instance(self):
        workflow = self.workflow

        if workflow.model_class is self.__class__:
            return self
        else:
            return workflow.model_class.objects.get(id=self.id)
