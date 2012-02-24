from datetime import datetime, date
from operator import attrgetter
from functools import partial

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.functional import Promise
from django.db.models.fields import FieldDoesNotExist
from django.core import serializers
from django.utils.simplejson import dumps as sj_dumps, loads
from django.utils.translation import force_unicode

from yawf.handlers import SerializibleHandlerResult


class CustomJSONEncoder(DjangoJSONEncoder):

    def default(self, o):
        if isinstance(o, Promise):
            return force_unicode(o)
        elif isinstance(o, datetime):
            return o.strftime("%Y-%m-%dT%H:%M:%S")
        elif isinstance(o, date):
            return o.strftime("%Y-%m-%d")
        elif isinstance(o, models.Model):
            if hasattr(o, 'natural_key'):
                return o.natural_key()
            else:
                return force_unicode(o.pk)
        elif isinstance(o, models.query.QuerySet):
            return map(attrgetter('pk'), o)
        elif isinstance(o, set):
            return list(o)
        elif isinstance(o, SerializibleHandlerResult):
            return o.get_serializible_value()
        else:
            return super(CustomJSONEncoder, self).default(o)

dumps = partial(sj_dumps, cls=CustomJSONEncoder)


def serialize(instance):
    serializer = serializers.get_serializer("json")()
    serializer.serialize([instance], ensure_ascii=False)
    return serializer.getvalue()


def deserialize_to_dict(content):
    item = loads(content)[0]
    return item['fields']


def deserialize(content, format_='json'):
    try:
        deserialized = serializers.deserialize(format_, content).next()
    except FieldDoesNotExist:
        return False, deserialize_to_dict(content)
    else:
        return True, deserialized


def json_converter(attr_name, getter=None, setter=None):
    """
    Returns property object which wraps given attr_name with json load/dump
    """

    if getter is not None:
        def json_getter(instance):
            json_str = getattr(instance, attr_name)
            return getter(loads(json_str)) if json_str is not None else None
    else:
        def json_getter(instance):
            json_str = getattr(instance, attr_name)
            return loads(json_str) if json_str is not None else None

    if setter is not None:
        def json_setter(instance, dict_):
            setattr(instance, attr_name, setter(dumps(dict_)))
    else:
        def json_setter(instance, dict_):
            setattr(instance, attr_name, dumps(dict_))

    return property(json_getter, json_setter)
