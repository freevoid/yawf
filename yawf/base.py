# -*- coding: utf-8 -*-
import warnings

from yawf import _register_workflow
from yawf.config import INITIAL_STATE, DEFAULT_START_MESSAGE
from yawf import permissions
from yawf.exceptions import (
    UnhandledMessageError,
)
from yawf.library import Library


def proxy_method(proxy_obj_attr, proxy_attr):

    def proxy_method(self, *args, **kwargs):
        proxy_obj = getattr(self, proxy_obj_attr)
        return getattr(proxy_obj, proxy_attr)(*args, **kwargs)

    return proxy_method


def form_for_model(model_cls):

    from django import forms

    class DefaultModelForm(forms.ModelForm):

        class Meta:
            model = model_cls

    return DefaultModelForm


class WorkflowMeta(type):

    def __new__(cls, name, bases, attrs):
        if ('extra_valid_states' in attrs and
                (len(bases) != 1 or (bases[0] is not object))):
            # warn about using extra_valid_states in derived classes
            attrs['states'] = attrs['extra_valid_states']
            attrs.pop('extra_valid_states')
            warnings.warn(
                'Use of extra_valid_states is DEPRECATED. Change your code to use states instead.',
                DeprecationWarning)
        return super(WorkflowMeta, cls).__new__(cls, name, bases, attrs)


class WorkflowBase(object):
    '''
    Basic class that defines request processing as extended fsm.

    State machine has states, actions, receives messages with parameters,
    know how to validate parameters basing on state and message id. State
    machine also has information about permission checks that sender must
    pass to be able to deliver his message.

    Logic splitted in several submodules of workflow package. This is
    basic class to inherit, that has methods to register callbacks and
    workflow context.
    '''

    __metaclass__ = WorkflowMeta

    rank = 0
    initial_state = INITIAL_STATE
    state_choices = None
    default_permission_checker = permissions.allow_to_all
    create_form_cls = None
    create_form_template = None
    verbose_name = None
    verbose_state_names = None
    state_attr_name = 'state'

    model_class = None

    exportable_fields = ('rank', 'verbose_name',)
    # message id or callable that returns message context to start workflow
    start_workflow = DEFAULT_START_MESSAGE

    @property
    def extra_valid_states(self):
        warnings.warn(
            'Use of extra_valid_states is DEPRECATED. Change your code to use states instead.',
            DeprecationWarning)
        return self.states

    def __init__(self, inherit_behaviour=False, id=None):

        if self.state_choices:
            self.verbose_state_names = dict(self.state_choices)
        elif self.verbose_state_names:
            self.state_choices = self.verbose_state_names.items()

        self.states = set(self.verbose_state_names.keys())
        self._valid_states = self.states.union([self.initial_state])

        if id is not None:
            self.id = id

        if self.create_form_cls is None:
            self.create_form_cls = form_for_model(self.model_class)

        self.inherit_behaviour = inherit_behaviour

        if inherit_behaviour:
            self._library = Library.proxy_library(self._library)
        else:
            self._library = Library()

        self._library.default_permission_checker = self.default_permission_checker
        self._library.states = self.states
        self._library.valid_states = self._valid_states

        super(WorkflowBase, self).__init__()
        _register_workflow(self)

    def is_valid_state(self, state):
        return state in self._valid_states

    def is_valid_message(self, state, message_id):
        try:
            self._library.get_handler(state, message_id)
        except UnhandledMessageError:
            return False
        else:
            return True

    @property
    def library(self):
        return self._library

    register_action = proxy_method('_library', 'effect')
    register_handler = proxy_method('_library', 'handler')
    register_message = proxy_method('_library', 'message')
    register_resource = proxy_method('_library', 'resource')
    register_message_by_form = proxy_method('_library', 'message_by_form')

    get_checkers_by_state = proxy_method('_library',
            'get_checkers_by_state')
    get_message_checkers_by_state = proxy_method('_library',
            'get_message_checkers_by_state')
    get_resource_checkers_by_state = proxy_method('_library',
            'get_resource_checkers_by_state')
    get_available_messages = proxy_method('_library',
            'get_available_messages')

    get_handler = proxy_method('_library', 'get_handler')
    get_action = proxy_method('_library', 'get_effect')
    get_possible_actions = proxy_method('_library', 'get_possible_effects')
    get_message_spec = proxy_method('_library', 'get_message_spec')
    get_resource = proxy_method('_library', 'get_resource')
    get_available_resources = proxy_method('_library', 'get_available_resources')
    get_available_messages = proxy_method('_library', 'get_available_messages')

    def get_message_specs(self):
        return self._library._message_specs

    def instance_fabric(self, sender, cleaned_data):
        return self.model_class(**cleaned_data)

    def post_create_hook(self, sender, cleaned_data, instance):
        pass

    def validate(self):

        assert self.model_class is not None
        #assert self._deferred or self._handlers
        #assert self._message_specs
        assert self.states
