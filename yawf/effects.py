import collections

__all__ = ['SideEffect']


class SideEffect(object):
    '''
    Basic class to express side-effect actions.

    SideEffect in yawf is a side-effect action that can be performed
    after certain changes in workflow.

    User can treat effects as event handlers and put that handlers on
    any transition. To specify a transition, one can specify a list of
    states before transition, a list of states after transition and a list of
    message ids. Everything above is optional, so if you register a default
    side-effect without specify any of this variables, such side-effect will
    be called after *each* transition.

    User can put any number of side-effects on each and every transition. In
    case of multiple effects matching specific transition each side-effect
    will be executed one by one.

    Yawf executes side-effect *after* state transition, when yawf obtains new
    state (and possibly modified object).

    Yawf passes keyword arguments to side-effect:
      * `old_obj`: the object *before* the state transition (before locking);
      * `obj`: the object *after* the state transition;
      * `sender`: message sender;
      * `params`: message arguments;
      * `message_spec`: message spec class (because we may want to distinguish
            between different messages in effects);
      * `extra_context`: extra context thas was passed to
            :py:func:`yawf.dispatch.dispatch`;
      * `handler_result`: result of the state transition routine.
    '''

    message_id = None
    message_group = None
    states_from = None
    states_to = None
    is_transactional = False

    def __init__(self, message_id=None,
            states_from=None, states_to=None,
            message_group=None):

        if message_id is not None:
            self.message_id = message_id
        if message_group is not None:
            self.message_group = message_group
        if states_to is not None:
            self.states_to = states_to
        if states_from is not None:
            self.states_from = states_from

        message_group = self.message_group

        if message_group is not None:
            if isinstance(message_group, basestring):
                self.message_group = [message_group]
            else:
                assert isinstance(message_group, collections.Iterable)

        super(SideEffect, self).__init__()

    def perform(self, **kwargs):
        return kwargs

    def set_performer(self, performer):
        self.perform = lambda **kwargs: performer(**kwargs)

    def __call__(self, **kwargs):
        return self.perform(**kwargs)

    @property
    def name(self):
        return self.__class__.__name__


# for backward-compatibility
SideEffectAction = SideEffect
