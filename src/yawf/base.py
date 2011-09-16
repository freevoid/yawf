# -*- coding: utf-8 -*-
import collections

from django.utils.datastructures import MergeDict

from yawf import _register_workflow
from yawf.config import INITIAL_STATE, DEFAULT_START_MESSAGE
from yawf import permissions
from yawf.actions import SideEffectAction
from yawf.resources import WorkflowResource
from yawf.exceptions import UnhandledMessageError, IllegalStateError,\
         MessageSpecNotRegisteredError

from yawf.messages.spec import MessageSpec
from yawf.permissions import OrChecker


def merge_container(container_name, container_fabric, parent_container):

    # XXX: need to test before extensive use


    if issubclass(container_fabric, dict):
        basic_container = container_fabric()
        if container_name == '_message_specs':
            class NewMergeDict(MergeDict):
                __setitem__ = basic_container.__setitem__

            container = NewMergeDict(basic_container, parent_container)
        else:
            container = parent_container

        return container
    else:
        return parent_container


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

    rank = 0
    valid_states = [INITIAL_STATE]
    extra_valid_states = ()
    default_permission_checker = staticmethod(permissions.allow_to_all)
    create_form_cls = None
    create_form_template = None
    verbose_name = None
    verbose_type_names = {}
    verbose_state_names = {}
    state_attr_name = 'state'

    exportable_fields = ('rank', 'verbose_name',)
    # message id or callable that returns message context to start workflow
    start_workflow = DEFAULT_START_MESSAGE

    _containers = (
            ('_handlers', dict),
            ('_resources', dict),
            ('_resources_by_state', dict),
            ('_resource_checkers_by_state', dict),
            ('_actions', dict),
            ('_actions_any_destination', dict),
            ('_actions_any_startpoint', dict),
            ('_actions_any_states', dict),
            ('_actions_for_possible', dict),
            ('_valid_states', set),
            ('_message_specs', dict),
            ('_message_checkers_by_state', dict))

    def __init__(self, inherit_behaviour=False, id=None):

        if not inherit_behaviour:
            self.init_containers()
        else:
            self.init_inherited_containers()

        if id is not None:
            self.id = id

        self.inherit_behaviour = inherit_behaviour
        super(WorkflowBase, self).__init__()
        _register_workflow(self)


    def init_inherited_containers(self):
        cls = self.__class__

        for container_name, container_fabric in self._containers:
            setattr(self, container_name,
                    merge_container(container_name, container_fabric, getattr(cls, container_name)))

        self._valid_states = set(cls._valid_states)
        self._valid_states.update(self.extra_valid_states)

    @classmethod
    def init_containers(cls):
        for container_name, container_fabric in cls._containers:
            setattr(cls, container_name, container_fabric())

        cls._valid_states = set(cls.valid_states)
        cls._valid_states.update(cls.extra_valid_states)


    def is_valid_state(self, state):
        return state in self._valid_states

    def is_valid_message(self, state, message_id):
        lookup_result = self._handlers.get(state)
        if lookup_result is None:
            if not self.is_valid_state(state):
                raise IllegalStateError(state)
            return False

        return message_id in lookup_result

    def get_verbose_type(self, state):
        return self.verbose_type_names.get(state)

    def get_nonfinal_states(self):
        return self._handlers.keys()

    def get_checkers_by_state(self, state):
        return self.get_message_checkers_by_state(state)\
                .union(self.get_resource_checkers_by_state(state))

    def get_message_checkers_by_state(self, state):
        return self._message_checkers_by_state.get(state, set())

    def get_resource_checkers_by_state(self, state):
        return self._resource_checkers_by_state.get(state, set())

    def get_available_messages(self, state):
        lookup_result = self._handlers.get(state)
        if lookup_result is None:
            if not self.is_valid_state(state):
                raise IllegalStateError(state)
            return ()

        return ((permission_checkers, message_id) for
                    message_id, (permission_checkers, _handler) in
                        lookup_result.iteritems())

    def get_available_resources(self, state):
        lookup_result = self._resources_by_state.get(state)
        if lookup_result is None:
            if not self.is_valid_state(state):
                raise IllegalStateError(state)
            return ()

        return lookup_result.itervalues()

    def get_resource(self, state, resource_id):
        '''
        Return resource object or None if there is no resource with given id
        for given state.
        '''
        lookup_result = self._resources_by_state.get(state)
        if lookup_result is None:
            if not self.is_valid_state(state):
                raise IllegalStateError(state)
            return None

        return lookup_result.get(resource_id)

    def get_handler(self, state, message_id):
        '''
        Return two-tuple of two callables: permission checker (takes
        sender and workflow object) and callable from handler's table.
        Takes incoming message id and current state.

        Handler callable gets workflow object, message sender and arbitrary
        keyword arguments (passed with message) and must return new
        state id based on this information (it can return None if
        message should be ignored). If handler returns a callable, then
        this callable applies as transaction on object (to change
        its state).

        If there are no handler for this message_id, raises
        UnhandledMessageError(message_id).

        If current state is illegal for this type of message, raises
        IllegalStateError(current_state).
        '''
        lookup_result = self._handlers.get(state)
        if lookup_result is None:
            raise IllegalStateError(state)

        complex_handler = lookup_result.get(message_id)

        if complex_handler is None:
            raise UnhandledMessageError(message_id, lookup_result.keys())

        permission_checkers, handler = complex_handler

        return OrChecker(*permission_checkers), handler

    def get_action(self, from_state, to_state, message_id):
        # TODO: refactor
        first_try = self._actions.get((from_state, to_state, message_id))
        if callable(first_try):
            return first_try

        second_try = self._actions_any_startpoint.get((to_state, message_id))
        if callable(second_try):
            return second_try

        pre_last_try = self._actions_any_destination.get((from_state, message_id))
        if callable(pre_last_try):
            return pre_last_try

        last_try = self._actions_any_states.get(message_id)
        if callable(last_try):
            return last_try

        return None

    def get_possible_actions(self, from_state, message_id):
        first_try = self._actions_for_possible.get((from_state, message_id))
        if first_try:
            return first_try

        last_try = self._actions_for_possible.get((None, message_id))
        return last_try or []

    def get_message_specs(self):
        return self._message_specs

    def get_message_spec(self, message_id):
        message_spec = self._message_specs.get(message_id)
        if message_spec is None:
            raise MessageSpecNotRegisteredError(message_id)
        return message_spec

    def register_resource(self, resource_id=None, description=None,
            available_in_states=None,
            permission_checker=None,
            slug=None):

        if permission_checker is None:
            permission_checker = (self.default_permission_checker,)

        if not isinstance(permission_checker, collections.Iterable):
            permission_checkers = (permission_checker,)
        else:
            permission_checkers = permission_checker

        if available_in_states is None:
            available_in_states = self._valid_states

        if not available_in_states:
            raise ValueError("available_in_states cannot be empty")

        def registrator(handler):

            if resource_id in self._resources:
                raise ValueError("Resource with that name already registered")

            resource = WorkflowResource(handler, resource_id=resource_id,
                    description=description,
                    permission_checkers=permission_checkers,
                    slug=slug)

            self._resources[resource_id] = resource

            for state in available_in_states:
                # add handler to lookup table by (state, message_id)
                resources = self._resources_by_state.setdefault(state, {})
                resources[resource_id] = resource

                checkers_set = self._resource_checkers_by_state.setdefault(
                        state, set())
                checkers_set.update(permission_checkers)

            return handler

        return registrator

    def register_message_by_form(self, message_id, base_spec=MessageSpec):

        def registrator(message_validator):

            class Spec(base_spec):
                id = message_id
                validator_cls = message_validator

            self.register_message(Spec)
            return message_validator

        return registrator

    def register_message(self, message_spec):
        if message_spec.id in self._message_specs:
            raise ValueError("Message spec already registered for message '%s'" %
                    (message_spec.id,))
        self._message_specs[message_spec.id] = message_spec
        return message_spec

    def register_handler(self, message_id=None, states_from=None,
            permission_checker=None):
        '''
        Returns decorator to register handler for message_id when fsm in
        one of the states in states_from and sender passed permission_checker.

        If states_from is None we register given handler for every valid state.

        permission_checker may be either callable or iterable of callables.
        In second case, all checkers are joined in single lambda function
        with logical OR rule.

        Permission checkers from iterable are indexed by state so that one
        can get all distinct checkers that must be evaluated to know what
        messages single sender can pass to fsm (see get_checkers_by_state
        method and functions in yawf.messages.allowed).
        '''

        if permission_checker is None:
            permission_checker = (self.default_permission_checker,)

        if not isinstance(permission_checker, collections.Iterable):
            permission_checkers = (permission_checker,)
        else:
            permission_checkers = permission_checker

        if states_from is None:
            states_from = self.valid_states

        def registrator(handler, message_id=message_id):
            if message_id is None:
                message_id = handler.__name__

            for state in states_from:
                # add handler to lookup table by (state, message_id)
                handlers = self._handlers.setdefault(state, {})
                handlers[message_id] = (permission_checkers, handler)

                # add checker to checkers_by_state index
                checkers_set = self._message_checkers_by_state.setdefault(state, set())
                checkers_set.update(permission_checkers)
            return handler

        return registrator

    def register_action_obj(self, action_obj):
        message_id = action_obj.message_id
        states_to, states_from = action_obj.states_to, action_obj.states_from

        if states_to is None:
            if states_from is not None:
                for state_from in states_from:
                    key = (state_from, message_id)
                    self._actions_any_destination[key] = action_obj
                    tmp = self._actions_for_possible.setdefault(key, [])
                    tmp.append(action_obj)
            else:
                key = message_id
                self._actions_any_states[key] = action_obj
                tmp = self._actions_for_possible.setdefault(key, [])
                tmp.append(action_obj)
        else:
            if states_from is None:
                for state_to in states_to:
                    key = (state_to, message_id)
                    self._actions_any_startpoint[key] = action_obj
                tmp = self._actions_for_possible.setdefault((None, message_id), [])
                tmp.append(action_obj)
            else:
                for state_to in states_to:
                    for state_from in states_from:
                        key = (state_from, state_to, message_id)
                        self._actions[key] = action_obj
                        tmp = self._actions_for_possible.setdefault((state_from, message_id), [])
                        tmp.append(action_obj)

    def register_action(self, message_id=None, states_from=None, states_to=None):

        if not isinstance(message_id, basestring) and issubclass(message_id, SideEffectAction):
            self.register_action_obj(message_id())
            return message_id

        action_obj = SideEffectAction(
            message_id=message_id,
            states_from=states_from,
            states_to=states_to)

        def registrator(action):

            if action_obj.message_id is None:
                action_obj.message_id = action.__name__

            action_obj.set_performer(action)
            self.register_action_obj(action_obj)
            return action

        return registrator

    def instance_fabric(self, sender, cleaned_data):
        return self.model_class(**cleaned_data)

    def post_create_hook(self, sender, cleaned_data, instance):
        pass

