from . import Message

class Submessage(object):

    need_lock_object = True

    def __init__(self, obj, message_id, sender, params=None, need_lock_object=True):
        self.obj = obj
        self.sender = sender
        self.message_id = message_id
        self.params = params
        self.need_lock_object = need_lock_object
        super(Submessage, self).__init__()

    def as_message(self, parent):

        return Message(self.sender, self.message_id,
            clean_params=self.params,
            parent_message_id=parent.unique_id,
            message_group=parent.message_group,
        )

    def dispatch(self, parent_obj, parent_message):
        from yawf.dispatch import dispatch_message
        message = self.as_message(parent_message)
        return dispatch_message(
            self.obj,
            message=message,
            defer_side_effect=True,
            need_lock_object=self.need_lock_object)


class RecursiveSubmessage(Submessage):

    def __init__(self, message_id, sender, params=None):
        super(RecursiveSubmessage, self).__init__(
            obj=None,
            sender=sender, message_id=message_id, params=params)

    def dispatch(self, parent_obj, parent_message):
        from yawf.dispatch import dispatch_message
        message = self.as_message(parent_message)
        return dispatch_message(
            parent_obj,
            message=message,
            defer_side_effect=True,
            need_lock_object=False)
