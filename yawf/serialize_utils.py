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


class CustomJSONEncoder(DjangoJSONEncoder):

    def default(self, o):
        if isinstance(o, Promise):
            return force_unicode(o)
        elif isinstance(o, datetime):
            return o.strftime("%Y-%m-%dT%H:%M:%S")
        elif isinstance(o, date):
            return o.strftime("%Y-%m-%d")
        elif isinstance(o, models.Model):
            return force_unicode(o.pk)
        elif isinstance(o, models.query.QuerySet):
            return map(attrgetter('pk'), o)
        elif isinstance(o, set):
            return list(o)
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


def deserialize(content):
    try:
        deserialized = serializers.deserialize("json", content).next()
    except FieldDoesNotExist:
        return False, deserialize_to_dict(content)
    else:
        return True, deserialized
