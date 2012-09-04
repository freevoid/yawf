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
    '''
    Specifies a message that can be passed to workflow.

    Basic class for one of main entities.
    Message spec knows:
      * it's unique ``id'';
      * how to represent spec for humans (using ``verb'' in __unicode__);
      * how to validate parameters for this message (using ``validator_cls'');
      * priority (``rank'' attribute).
    '''
    # unique (in scope of single workflow) message id (typically str)
    id = None
    # human-friendly name for action
    verb = None
    # validator class -- with django.forms.Form interface
    validator_cls = EmptyValidator
    # rank used to sort specs
    rank = 0

    id_grouper = '__'
    is_grouped = False

    def __init__(self, **attrs):
        super(MessageSpec, self).__init__()

        if hasattr(self, 'Validator'):
            self.validator_cls = self.Validator

        for attr, value in attrs.iteritems():
            setattr(self, attr, value)

        grouper = self.id_grouper
        message_id = self.id

        if message_id is None:
            raise ValueError(
                'You must specify not-None id for MessageSpec subclass')
        else:
            if grouper in message_id:
                self.group_path = message_id.split(grouper)
                self.is_grouped = True
            else:
                self.group_path = [message_id]
                self.is_grouped = False

            if self.verb is None:
                self.verb = self.id

    def params_wrapper(self, params):
        '''
        Wrapper used to wrap cleaned_data returned by validator_cls
        before passing it to handler.

        With wrapper one has additional layer to transform structure of
        cleaned_data dict to make it more convenient to use.

        For example, see yawf.messages.common.BasicEditMessage class.
        '''
        return params

    def dehydrate_params(self, obj, message):
        '''
        Method, that returns dehydrated message params for serialization.
        '''
        return None

    def __unicode__(self):
        return unicode(self.verb)

    def __repr__(self):
        return u'<%s: %s>' % (self.__class__.__name__, self)
