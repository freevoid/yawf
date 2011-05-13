from yawf.exceptions import ResourcePermissionDeniedError


class WorkflowResource(object):

    def __init__(self, handler, resource_id, permission_checkers,
                                                description=None):
        super(WorkflowResource, self).__init__()
        self._handler = handler
        self.id = resource_id
        self.checkers = permission_checkers
        self.permission_checker = lambda gap, sender:\
                                  all(c(gap, sender) for c in permission_checkers)
        self.description = description

    def __call__(self, request, obj, sender):

        if self.permission_checker(obj, sender):
            return self._handler(request, obj, sender)
        else:
            raise ResourcePermissionDeniedError(self.id,
                    obj, sender)
