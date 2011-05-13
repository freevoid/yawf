class EmptyValidator(object):
    '''
    Class with django-form behaviour that filters out all incoming data,
    always becomes valid and returns empty dict as cleaned data.
    '''

    def __init__(self, *args, **kwargs):
        super(EmptyValidator, self).__init__()

    def is_valid(self):
        return True

    @property
    def cleaned_data(self):
        return {}


class MessageSpec(object):

    id = None
    verb = None
    validator_cls = EmptyValidator
    rank = 0

    @classmethod
    def params_wrapper(cls, params):
        return params
