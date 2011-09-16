from functools import wraps, partial

from yawf.config import STATE_TYPE_CONSTRAINT
from yawf import get_workflow_by_instance


def chained_apply(callables_iterable):
    def chained_wrapper(*args, **kwargs):
        for fun in callables_iterable:
            fun(*args, **kwargs)
    return chained_wrapper


def make_common_updater(kwargs, field_names=None):

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

    return common_updater


def common_cancel(obj, soft_delete_attr=None):
    obj.state = 'canceled'
    if soft_delete_attr:
        setattr(obj, soft_delete_attr, True)
    obj.save()


def common_start(obj, state, soft_delete_attr=None):
    obj.state = state
    if soft_delete_attr:
        setattr(obj, soft_delete_attr, False)
    obj.save()


def make_common_cancel(soft_delete_attr=None):

    return partial(common_cancel,
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
    sql, params = queryset.query.get_compiler(queryset.db).as_sql()
    return queryset.model._default_manager.raw(sql.rstrip() + ' FOR UPDATE',
            params)
