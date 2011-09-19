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


class MessageSpecMeta(type):
    '''
    MessageSpec metaclass to support inline validators.

    If message spec defines inline class with name ``Validator'', it
    would be used instead of ``validator_cls''.
    '''

    def __new__(cls, name, bases, attrs):
        if 'Validator' in attrs:
            attrs['validator_cls'] = attrs['Validator']
        return super(MessageSpecMeta, cls).__new__(cls, name, bases, attrs)


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

    # meta used to support inline Validator
    __metaclass__ = MessageSpecMeta

    # unique (in scope of single workflow) message id (typically str)
    id = None
    # human-friendly name for action
    verb = None
    # validator class -- with django.forms.Form interface
    validator_cls = EmptyValidator
    # rank used to sort specs
    rank = 0

    @classmethod
    def params_wrapper(cls, params):
        '''
        Wrapper used to wrap cleaned_data returned by validator_cls
        before passing it to handler.

        With wrapper one has additional layer to transform structure of
        cleaned_data dict to make it more convenient to use.

        For example, see yawf.messages.common.BasicEditMessage class.
        '''
        return params

    def __unicode__(self):
        return unicode(self.verb)

    def __repr__(self):
        return u'<%s: %s>' % (self.__class__.__name__, self)
