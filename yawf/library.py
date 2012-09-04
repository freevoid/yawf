import collections
import inspect
from functools import wraps
from operator import attrgetter

from django.utils.datastructures import MergeDict
from django.utils.importlib import import_module

from yawf.effects import SideEffect
from yawf.handlers import Handler
from yawf.resources import WorkflowResource
from yawf.exceptions import (
    UnhandledMessageError,
    IllegalStateError,
    MessageSpecNotRegisteredError,
    GroupPathEmptyError,
)
from yawf.messages.spec import MessageSpec
from yawf.messages.common import message_spec_fabric
from yawf.permissions import OrChecker
from yawf.utils import metadefaultdict, maybe_list


def merge_container(container_name, container_fabric, parent_container):

    # XXX: need to test before extensive use

    if inspect.isclass(container_fabric) and issubclass(container_fabric, dict):
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


def touches_index(method):

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self._is_index_built:
            if not self._is_imported_registrants:
                self.import_registrants()
            self.rebuild_index()
        return method(self, *args, **kwargs)

    return wrapper


def need_imports(method):

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self._is_imported_registrants:
            self.import_registrants()
        return method(self, *args, **kwargs)

    return wrapper


class Library(object):

    _is_index_built = False
    _is_imported_registrants = False

    _containers = (
        ('_resources', dict),
        ('_resources_by_state', dict),
        ('_message_specs', dict),
        ('_message_groups', dict),
        ('_handler_patterns', list),
        ('_effect_patterns', list),
        ('_resource_checkers_index', metadefaultdict(set)),
        ('_registered_message_id_set', set),
    )

    _index_containers = (
        ('_handler_index', metadefaultdict(list)),
        ('_handler_message_index', metadefaultdict(metadefaultdict(list))),
        ('_handler_state_index', metadefaultdict(metadefaultdict(list))),
        ('_message_checkers_index', metadefaultdict(set)),
        ('_effect_index', metadefaultdict(list)),
        ('_deferrable_effect_index', metadefaultdict(list)),
        ('_transactional_effect_index', metadefaultdict(list)),
        ('_possible_effect_index', metadefaultdict(list)),
    )

    def __init__(self, registrants=()):
        self._init_containers()
        if registrants:
            self._registrants = registrants
        else:
            self._registrants = ()
        super(Library, self).__init__()

    def import_registrants(self):
        for dotted_name in self._registrants:
            import_module(dotted_name)
        self._is_imported_registrants = True

    @classmethod
    def proxy_library(cls, base, *bases):

        self = cls()
        for container_name, container_fabric in self._containers:

            merged_container = merge_container(
                container_name,
                container_fabric,
                getattr(base, container_name))

            for extra_base in bases:
                merged_container = merge_container(
                    container_name,
                    lambda: merged_container,
                    getattr(extra_base, container_name))

            setattr(self, container_name, merged_container)

        return self

    def message(self, message_spec):

        to_return = message_spec

        if inspect.isclass(message_spec) and\
                issubclass(message_spec, MessageSpec):
            message_spec = message_spec()

        if not isinstance(message_spec, MessageSpec):
            raise TypeError('Message spec must be an instance or a subclass of MessageSpec')

        # register in flat registry
        if message_spec.id in self._registered_message_id_set:
            raise ValueError("Message spec already registered for message '%s'" %
                    (message_spec.id,))
        self._registered_message_id_set.add(message_spec.id)
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

        if self._is_index_built:
            self.rebuild_index()

        return to_return

    def message_by_form(self, message_id=None, message_id_list=None,
            base_spec=MessageSpec, **attrs):

        if message_id is None:
            if message_id_list is None:
                raise ValueError("You must specify either message_id or message_id_list")
        else:
            message_id_list = [message_id]

        def registrator(message_validator):

            for message_id in message_id_list:
                spec_cls = message_spec_fabric(
                    message_id,
                    base_spec=base_spec,
                    validator_cls=message_validator,
                    **attrs)

                self.message(spec_cls)
            return message_validator

        return registrator

    def resource(self, resource_id=None, description=None,
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
            available_in_states = self.states

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
                self._resource_checkers_index[state].update(
                    permission_checker.get_atomical_checkers())

            return handler

        return registrator

    def handler(self, message_id=None, **options):
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
        return self._meta_register(Handler, self._register_handler_obj,
                message_id=message_id, **options)

    def effect(self,
            message_id=None, **options):

        return self._meta_register(SideEffect, self._register_effect_obj,
                message_id=message_id, **options)

    def rebuild_index(self):
        self._init_index_containers()

        # Build index for handlers
        for pattern in self._handler_patterns:
            message_id_list, group_path, states_from, handler = pattern

            message_id_list = list(message_id_list)
            if group_path:
                message_id_list.extend(
                    self._get_message_ids_by_path(group_path))

            if not states_from:
                states_from = self.states

            for message_id in message_id_list:
                for state in states_from:

                    self._handler_index[(state, message_id)].append(handler)
                    self._handler_message_index[message_id][state].append(handler)
                    self._handler_state_index[state][message_id].append(handler)
                    # add checker to checkers index
                    self._message_checkers_index[state].update(
                        handler.permission_checker.get_atomical_checkers())

        # Build index for effects
        for pattern in self._effect_patterns:
            message_id_list, group_path, states_to, states_from, effect = pattern

            message_id_list = list(message_id_list)
            if group_path:
                message_id_list.extend(
                    self._get_message_ids_by_path(group_path))

            if not states_from:
                states_from = self.states

            if not states_to:
                states_to = self.states

            # if message specs not specified, stick to any registered message
            if not message_id_list:
                message_id_list = self._registered_message_id_set

            for message_id in message_id_list:

                for state_from in states_from:

                    key = (state_from, message_id)
                    self._possible_effect_index[key].append(effect)

                    for state_to in states_to:
                        key = (state_from, state_to, message_id)
                        self._effect_index[key].append(effect)
                        if effect.is_transactional:
                            self._transactional_effect_index[key].append(effect)
                        else:
                            self._deferrable_effect_index[key].append(effect)

        self._is_index_built = True

    def get_handler(self, state, message_id):
        return self.get_handlers(state, message_id)[0]

    @touches_index
    def get_handlers(self, state, message_id):
        '''
        Return Handler instances to handle ``message_id'' for workflow in state
        ``state''.

        :param state:
            Current basic state of workflow.
        :param message_id:
            id of incoming message.

        If there are no handler for this message_id, raises
        UnhandledMessageError(message_id).
        '''
        key = (state, message_id)
        handlers = self._handler_index.get(key)

        if not handlers:
            if state is None:
                return self._handler_message_index.get(message_id, [])
            elif message_id is None:
                return self._handler_state_index.get(state, [])
            else:
                raise UnhandledMessageError(message_id)

        return handlers

    def get_effect(self, from_state, to_state, message_id):
        effects = self.get_effects(from_state, to_state, message_id)
        if effects:
            return effects[0]

    @touches_index
    def get_effects(self, from_state, to_state, message_id):
        key = (from_state, to_state, message_id)
        return self._effect_index.get(key)

    @touches_index
    def get_effects_for_transition(self, from_state, to_state, message_id):
        key = (from_state, to_state, message_id)
        return (self._transactional_effect_index.get(key),
                self._deferrable_effect_index.get(key))

    @touches_index
    def get_possible_effects(self, from_state, message_id):
        return self._possible_effect_index.get((from_state, message_id)) or []

    @need_imports
    def get_message_spec(self, message_id):
        '''
        Get registered message spec class with given id.

        Id can be iterable representing group path to the desired message.
        '''
        if not isinstance(message_id, basestring) and\
                isinstance(message_id, collections.Iterable):
            return self._get_message_spec_by_path(message_id)

        message_spec = self._message_specs.get(message_id)
        if message_spec is None:
            raise MessageSpecNotRegisteredError(message_id)
        return message_spec

    @need_imports
    def get_message_specs(self):
        return self._message_specs

    @need_imports
    def get_possible_message_ids(self):
        return self._registered_message_id_set

    def get_resource(self, state, resource_id):
        '''
        Return resource object or None if there is no resource with given id
        for given state.
        '''
        lookup_result = self._resources_by_state.get(state)
        if lookup_result is None:
            if state not in self.valid_states:
                raise IllegalStateError(state)
            return None

        return lookup_result.get(resource_id)

    def get_available_resources(self, state):
        lookup_result = self._resources_by_state.get(state)
        if lookup_result is None:
            if state not in self.valid_states:
                raise IllegalStateError(state)
            return ()

        return lookup_result.itervalues()

    def get_available_messages(self, state):

        lookup_result = self.get_handlers(state, None)

        if not lookup_result:
            if state not in self.valid_states:
                raise IllegalStateError(state)
            return ()

        return ((_handler.permission_checker, message_id)
                for message_id, _handlers in
                    lookup_result.iteritems()
                        for _handler in _handlers
                        if message_id in self._registered_message_id_set)

    def get_checkers_by_state(self, state):
        return self.get_message_checkers_by_state(state)\
                .union(self.get_resource_checkers_by_state(state))

    @touches_index
    def get_message_checkers_by_state(self, state):
        return self._message_checkers_index[state]

    def get_resource_checkers_by_state(self, state):
        return self._resource_checkers_index[state]

    @touches_index
    def iter_handlers(self):
        return self._handler_index.iteritems()

    @touches_index
    def iter_effects(self):
        return self._effect_index.iteritems()

    def _meta_register(self, reg_cls, registrator, message_id, **options):

        if inspect.isclass(message_id) and\
                issubclass(message_id, reg_cls):
            registrator(message_id())
            return message_id

        if isinstance(message_id, reg_cls):
            registrator(message_id)
            return message_id

        def _registrator(func):

            if message_id is None:
                _message_id = func.__name__
            else:
                _message_id = message_id

            obj = reg_cls(
                message_id=_message_id,
                **options)

            obj.set_performer(func)
            registrator(obj)
            return func

        if inspect.isfunction(message_id):
            func = message_id
            message_id = None
            return _registrator(func)
        else:
            return _registrator

    def _register_handler_obj(self, handler):

        if handler.permission_checker is None:
            handler.permission_checker = OrChecker(
                self.default_permission_checker)

        group_path = handler.message_group
        message_id_list = maybe_list(handler.message_id)

        self._handler_patterns.append(
            (message_id_list, group_path, handler.states_from, handler)
        )

        if self._is_index_built:
            self.rebuild_index()

        return handler

    def _register_effect_obj(self, effect):

        group_path = effect.message_group
        message_id_list = maybe_list(effect.message_id)
        states_to, states_from = effect.states_to, effect.states_from

        self._effect_patterns.append(
            (message_id_list, group_path, states_to, states_from, effect)
        )

        if self._is_index_built:
            self.rebuild_index()

        return effect

    def _get_message_spec_by_path(self, group_path):
        cur_level = self._message_groups
        for group_id in group_path:
            cur_level = cur_level.get(group_id, None)
            if not cur_level:
                raise GroupPathEmptyError(group_path)
        return cur_level

    def _get_message_ids_by_path(self, group_path):
        cur_level = self._message_groups
        for group_id in group_path:
            cur_level = cur_level.get(group_id, None)
            if not cur_level:
                return []
        return map(attrgetter('id'), cur_level.itervalues())

    def _init_containers(self):
        for container_name, container_fabric in self._containers:
            setattr(self, container_name, container_fabric())

    def _init_index_containers(self):
        for container_name, container_fabric in self._index_containers:
            setattr(self, container_name, container_fabric())
