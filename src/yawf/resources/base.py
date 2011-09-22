from yawf.exceptions import ResourcePermissionDeniedError


class WorkflowResource(object):

    def __init__(self, handler, resource_id, permission_checker,
                                                description=None,
                                                slug=None):
        super(WorkflowResource, self).__init__()
        self._handler = handler
        self.id = resource_id
        self.permission_checker = permission_checker
        self.description = description
        self.slug = slug or self.id

    def __call__(self, request, obj, sender):

        if self.permission_checker(obj, sender):
            return self._handler(request, obj, sender)
        else:
            raise ResourcePermissionDeniedError(self.id,
                    obj, sender)
