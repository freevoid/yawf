from yawf.messages.cleaning import clean_message_data

class Message(object):

    def __init__(self, sender, message_id, raw_params=None):
        self.sender = sender
        self.id = message_id
        self.raw_params = raw_params if raw_params is not None else {}
        self.params = None
        super(Message, self).__init__()
