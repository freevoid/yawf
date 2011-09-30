# -*- coding: utf-8 -*-
import collections
from operator import attrgetter
import warnings

from django.utils.datastructures import MergeDict

from yawf import _register_workflow
from yawf.config import INITIAL_STATE, DEFAULT_START_MESSAGE
from yawf import permissions
from yawf.actions import SideEffect
from yawf.handlers import Handler
from yawf.resources import WorkflowResource
from yawf.exceptions import (
    UnhandledMessageError,
    IllegalStateError,
    MessageSpecNotRegisteredError,
    GroupPathEmptyError,
)
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
    states = ()
    default_permission_checker = permissions.allow_to_all
    create_form_cls = None
    create_form_template = None
    verbose_name = None
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
            ('_message_specs', dict),
            ('_message_groups', dict),
            ('_deferred', list),
            ('_message_checkers_by_state', dict))

    @property
    def extra_valid_states(self):
        warnings.warn(
            'Use of extra_valid_states is DEPRECATED. Change your code to use states instead.',
            DeprecationWarning)
        return self.states

    def __init__(self, inherit_behaviour=False, id=None):

        if not inherit_behaviour:
            self.init_containers()
        else:
            self.init_inherited_containers()

        self.states = set(self.states)
        self._valid_states = self.states.union([self.initial_state])

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

    @classmethod
    def init_containers(cls):
        for container_name, container_fabric in cls._containers:
            setattr(cls, container_name, container_fabric())

    def _clean_deferred_chain(self):
        for df in self._deferred:
            df()
        self._deferred = []

    def is_valid_state(self, state):
        return state in self._valid_states

    def is_valid_message(self, state, message_id):
        self._clean_deferred_chain()
        lookup_result = self._handlers.get(state)
        if lookup_result is None:
            if not self.is_valid_state(state):
                raise IllegalStateError(state)
            return False

        return message_id in lookup_result


    def get_message_spec_by_path(self, group_path):
        cur_level = self._message_groups
        for group_id in group_path:
            cur_level = cur_level.get(group_id, None)
            if not cur_level:
                raise GroupPathEmptyError(group_path)
        return cur_level

    def get_message_ids_by_path(self, group_path):
        cur_level = self._message_groups
        for group_id in group_path:
            cur_level = cur_level.get(group_id, None)
            if not cur_level:
                raise GroupPathEmptyError(group_path)
        return map(attrgetter('id'), cur_level.itervalues())

    def get_nonfinal_states(self):
        self._clean_deferred_chain()
        return self._handlers.keys()

    def get_checkers_by_state(self, state):
        return self.get_message_checkers_by_state(state)\
                .union(self.get_resource_checkers_by_state(state))

    def get_message_checkers_by_state(self, state):
        return self._message_checkers_by_state.get(state, set())

    def get_resource_checkers_by_state(self, state):
        return self._resource_checkers_by_state.get(state, set())

    def get_available_messages(self, state):
        self._clean_deferred_chain()
        lookup_result = self._handlers.get(state)
        if lookup_result is None:
            if not self.is_valid_state(state):
                raise IllegalStateError(state)
            return ()

        return ((_handler.permission_checker, message_id) for
                    message_id, _handler in
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
        Return Handler instance to handle ``message_id'' for workflow in state
        ``state''.

        :param state:
            Current basic state of workflow.
        :param message_id:
            id of incoming message.

        If there are no handler for this message_id, raises
        UnhandledMessageError(message_id).

        If current state is illegal for this type of message, raises
        IllegalStateError(current_state).
        '''
        self._clean_deferred_chain()

        lookup_result = self._handlers.get(state)
        if lookup_result is None:
            raise IllegalStateError(state)

        handler = lookup_result.get(message_id)

        if handler is None:
            raise UnhandledMessageError(message_id, lookup_result.keys())

        return handler

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
        '''
        Get registered message spec class with given id.

        Id can be iterable representing group path to the desired message.
        '''
        if not isinstance(message_id, basestring) and\
                isinstance(message_id, collections.Iterable):
            return self.get_message_spec_by_path(message_id)

        message_spec = self._message_specs.get(message_id)
        if message_spec is None:
            raise MessageSpecNotRegisteredError(message_id)
        return message_spec

    def get_handlers(self):
        self._clean_deferred_chain()
        return self._handlers

    def register_resource(self, resource_id=None, description=None,
            available_in_states=None,
            permission_checker=None,
            slug=None):

        if permission_checker is None:
            permission_checker = OrChecker(self.default_permission_checker)
        elif not isinstance(permission_checker, collections.Iterable):
            permission_checker = OrChecker(permission_checker)
        else:
            permission_checker = OrChecker(*permission_checker)

        if available_in_states is None:
            available_in_states = self._valid_states

        if not available_in_states:
            raise ValueError("available_in_states cannot be empty")

        def registrator(handler):

            if resource_id in self._resources:
                raise ValueError("Resource with that name already registered")

            resource = WorkflowResource(handler, resource_id=resource_id,
                    description=description,
                    permission_checker=permission_checker,
                    slug=slug)

            self._resources[resource_id] = resource

            for state in available_in_states:
                # add handler to lookup table by (state, message_id)
                resources = self._resources_by_state.setdefault(state, {})
                resources[resource_id] = resource

                checkers_set = self._resource_checkers_by_state.setdefault(
                        state, set())
                checkers_set.update(permission_checker.get_atomical_checkers())

            return handler

        return registrator

    def register_message_by_form(self, message_id=None, message_id_list=None, base_spec=MessageSpec):

        if message_id is None:
            if message_id_list is None:
                raise ValueError("You must specify either message_id or message_id_list")
        else:
            message_id_list = [message_id]

        def registrator(message_validator):

            for message_id in message_id_list:
                class Spec(base_spec):
                    id = message_id
                    validator_cls = message_validator

                self.register_message(Spec)
            return message_validator

        return registrator

    def register_message(self, message_spec):

        # register in flat registry

        if message_spec.id in self._message_specs:
            raise ValueError("Message spec already registered for message '%s'" %
                    (message_spec.id,))
        self._message_specs[message_spec.id] = message_spec

        # handle message grouping

        if message_spec.is_grouped:
            group_path, final_id = message_spec.group_path[:-1],\
                                   message_spec.group_path[-1]

            group_dict = self._message_groups

            for group in group_path:
                group_dict = group_dict.setdefault(
                    group, {})

            if final_id in group_dict:
                raise ValueError("Message spec already registered for message '%s' in group '%s'" %
                    (final_id, group_path))

            group_dict[final_id] = message_spec

        return message_spec

    def register_handler(self, message_id=None, states_from=None,
            permission_checker=None, message_group=None,
            replace_if_exists=False,
            defer=True):
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

        # NOTE: isinstance(foo, ClassType) doesn't work with custom metaclasses
        if hasattr(message_id, '__bases__') and\
                issubclass(message_id, Handler):
            self.register_handler_obj(message_id(),
                replace_if_exists=message_id.replace_if_exists,
                defer=message_id.defer)
            return message_id

        def registrator(handler_func):

            if message_id is None:
                _message_id = handler_func.__name__
            else:
                _message_id = message_id

            handler_obj = Handler(
                message_id=_message_id,
                states_from=states_from,
                permission_checker=permission_checker,
                message_group=message_group)

            handler_obj.set_handler(handler_func)
            self.register_handler_obj(handler_obj,
                replace_if_exists=replace_if_exists,
                defer=defer)
            return handler_func

        return registrator

    def register_handler_obj(self, handler, replace_if_exists=False, defer=True):
        if handler.permission_checker is None:
            handler.permission_checker = OrChecker(
                self.default_permission_checker)

        if handler.states_from is None:
            # defaulting states_from to any extra state
            handler.states_from = self.states

        if defer:
            deferred = lambda: self._handler_registrator(handler)
            self._deferred.append(deferred)
        else:
            self._handler_registrator(handler)

        return handler

    def _handler_registrator(self, handler, replace_if_exists=False):
        group_path = handler.message_group

        if group_path is not None:
            message_id_list = self.get_message_ids_by_path(group_path)
        else:
            message_id_list = []

        if handler.message_id is not None:
            if isinstance(handler.message_id, basestring):
                message_id_list.append(handler.message_id)
            elif isinstance(handler.message_id, collections.Iterable):
                message_id_list.extend(handler.message_id)
            else:
                raise ValueError("Message id of unexpected type: %s" %
                        handler.message_id)

        for state in handler.states_from:
            # add handler to lookup table by (state, message_id)
            handlers = self._handlers.setdefault(state, {})
            for message_id in message_id_list:
                if message_id in handlers and not replace_if_exists:
                    raise ValueError(
                        "Handler for state %s, message %s already registered"
                            % (state, message_id))
                handlers[message_id] = handler

            # add checker to checkers_by_state index
            checkers_set = self._message_checkers_by_state.setdefault(
                state, set())
            checkers_set.update(
                handler.permission_checker.get_atomical_checkers())
        return handler

    def register_action_obj(self, action_obj, defer=True):

        if defer:
            deferred = lambda: self._action_registrator(action_obj)
            self._deferred.append(deferred)
        else:
            self._action_registrator(action_obj)

        return action_obj

    def _action_registrator(self, action_obj):

        group_path = action_obj.message_group

        if group_path is not None:
            message_id_list = self.get_message_ids_by_path(group_path)
        else:
            message_id_list = []

        if action_obj.message_id is not None:
            if isinstance(action_obj.message_id, basestring):
                message_id_list.append(action_obj.message_id)
            elif isinstance(action_obj.message_id, collections.Iterable):
                message_id_list.extend(action_obj.message_id)
            else:
                raise ValueError("Message id of unexpected type: %s" %
                        action_obj.message_id)

        states_to, states_from = action_obj.states_to, action_obj.states_from

        for message_id in message_id_list:
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

    def register_action(self,
            message_id=None, message_group=None,
            states_from=None, states_to=None):

        if issubclass(message_id, SideEffect):
            self.register_action_obj(message_id())
            return message_id

        def registrator(action):

            if message_id is None:
                _message_id = action.__name__
            else:
                _message_id = message_id

            action_obj = SideEffect(
                message_id=_message_id,
                states_from=states_from,
                states_to=states_to,
                message_group=message_group)

            action_obj.set_performer(action)
            self.register_action_obj(action_obj)
            return action

        return registrator

    def instance_fabric(self, sender, cleaned_data):
        return self.model_class(**cleaned_data)

    def post_create_hook(self, sender, cleaned_data, instance):
        pass

    def validate(self):

        assert self.model_class is not None
        assert self._deferred or self._handlers
        assert self._message_specs
        assert self.states
