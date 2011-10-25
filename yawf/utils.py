from itertools import ifilter
from collections import defaultdict, Iterable
from operator import attrgetter
from functools import wraps, partial
import types

from yawf.config import STATE_TYPE_CONSTRAINT
from yawf import get_workflow_by_instance


def chained_apply(callables_iterable):
    def chained_wrapper(*args, **kwargs):
        for fun in callables_iterable:
            fun(*args, **kwargs)
    return chained_wrapper


def make_common_updater(kwargs, field_names=None, post_hook=None):

    # to ensure that we will update, not insert new
    kwargs.pop('id', None)
    kwargs.pop('pk', None)

    if field_names:
        def common_updater(obj):
            for field_name in field_names:
                value = kwargs.get(field_name, '__missing')
                if value != '__missing':
                    setattr(obj, field_name, value)

            obj.save()

            if callable(post_hook):
                return post_hook(obj)
    else:
        def common_updater(obj):

            for field_name in (f.name for f in obj._meta.fields):
                value = kwargs.get(field_name, '__missing')
                if value != '__missing':
                    setattr(obj, field_name, value)

            for field_name in (f.name for f in obj._meta.many_to_many):
                value = kwargs.get(field_name)
                if value is not None:
                    setattr(obj, field_name, value)

            obj.save()

            if callable(post_hook):
                return post_hook(obj)

    return common_updater


def common_cancel(obj, cancel_state='canceled', soft_delete_attr=None):
    obj.state = cancel_state
    if soft_delete_attr:
        setattr(obj, soft_delete_attr, True)
    obj.save()


def common_start(obj, state, soft_delete_attr=None):
    obj.state = state
    if soft_delete_attr:
        setattr(obj, soft_delete_attr, False)
    obj.save()


def make_common_cancel(cancel_state='canceled', soft_delete_attr=None):

    return partial(common_cancel,
        cancel_state=cancel_state,
        soft_delete_attr=soft_delete_attr)


def make_common_start(state, soft_delete_attr=None):

    return partial(common_start,
        state=state, soft_delete_attr=soft_delete_attr)


def optionally_edit(handler):

    @wraps(handler)
    def wrapper(obj, sender, edit_fields=None, **kwargs):

        handler_result = handler(obj, sender, **kwargs)
        workflow = get_workflow_by_instance(obj)

        if not edit_fields:
            return handler_result
        else:
            if isinstance(handler_result, STATE_TYPE_CONSTRAINT):
                edit_fields['state'] = handler_result
                return workflow.make_updater(edit_fields)
            else:
                assert callable(handler_result)
                updater = workflow.make_updater(edit_fields)
                return chained_apply((updater, handler_result))

    return wrapper


def select_for_update(queryset):
    return queryset.select_for_update()


def model_diff(instance1, instance2):
    diff = []

    # Check only editable fields in model
    for field in ifilter(attrgetter('editable'), instance1._meta.fields):
        field_name = field.name
        value1 = getattr(instance1, field_name)
        value2 = getattr(instance2, field_name)
        if value1 != value2:
            diff.append({'field_name': field_name,
                    'field_verbose_name': field.verbose_name,
                    'old': value1, 'new': value2})

    return diff


def model_diff_fields(instance1, instance2):
    # Check only editable fields in model
    for field in ifilter(attrgetter('editable'), instance1._meta.fields):

        field_name = field.name
        value1 = getattr(instance1, field_name)
        value2 = getattr(instance2, field_name)
        if value1 != value2:
            yield field_name


def memoizible_property(getter):

    key = '_cache_prop_' + getter.__name__

    def getter_wrapper(self, *args, **kwargs):

        if not hasattr(self, key):
            result = getter(self, *args, **kwargs)
            if isinstance(result, types.GeneratorType):
                result = list(result)
            setattr(self, key, result)
            return result
        return getattr(self, key)

    return property(getter_wrapper)


def maybe_list(a):

    if a is not None:
        if isinstance(a, basestring) or not isinstance(a, Iterable):
            return [a]
        else:
            return list(a)
    else:
        return []


def metadefaultdict(fabric):
    return lambda: defaultdict(fabric)
