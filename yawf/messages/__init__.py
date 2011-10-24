import uuid


class Message(object):

    def __init__(self, sender, message_id,
            raw_params=None, message_group=None, parent_message_id=None):
        self.sender = sender
        self.id = message_id
        self._unique_id = None
        self.raw_params = raw_params if raw_params is not None else {}
        self.params = None
        self.parent_message_id = parent_message_id
        self.message_group = message_group\
            if message_group is not None else self.unique_id
        super(Message, self).__init__()

    @property
    def unique_id(self):
        '''
        Property that returns the unique identifier for message.

        Internally it uses UUID.
        '''
        if not self._unique_id:
            self._unique_id = uuid.uuid1()
        return self._unique_id


from .cleaning import clean_message_data
from .submessage import Submessage
