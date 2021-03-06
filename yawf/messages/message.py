import uuid

from yawf.exceptions import MessageValidationError

__all__ = ['Message']


class Message(object):

    def __init__(self, sender, message_id,
            raw_params=None, message_group=None, parent_message_id=None,
            clean_params=None):
        self.sender = sender
        self.id = message_id
        self._unique_id = None
        self.raw_params = raw_params if raw_params is not None else {}
        self.clean_params = clean_params if clean_params is not None else None
        self.params = None
        self.dehydrated_params = None
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

    def clean(self, workflow, obj):
        message_spec = workflow.get_message_spec(self.id)

        if self.clean_params is None:
            validator_cls = message_spec.validator_cls
            validator = validator_cls(self.raw_params)

            if validator.is_valid():
                self.clean_params = validator.cleaned_data
            else:
                raise MessageValidationError(validator)

        self.params = message_spec.params_wrapper(self.clean_params)
        # fix id in case it was a list (group path)
        self.id = message_spec.id
        self.spec = message_spec

        return self

    def dehydrate_params(self, workflow, obj):
        if self.params is None:
            raise RuntimeError(
                'Method dehydrate_params cannot be invoked before clean')

        self.dehydrated_params = self.spec.dehydrate_params(obj, self)
        return self
