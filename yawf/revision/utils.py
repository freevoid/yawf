import itertools as itr

from django.utils.functional import SimpleLazyObject
from reversion.models import Version

from yawf.utils import model_diff_fields, model_diff
from yawf.serialize_utils import deserialize


def diff_fields(old, new):
    # If content type doesn't match, we can't tell the difference
    if new.content_type_id != old.content_type_id:
        return None

    is_new_full, new = deserialize(new.serialized_data)
    is_old_full, old = deserialize(old.serialized_data)

    if is_new_full and is_old_full:
        return model_diff_fields(old.object, new.object)


def versions_diff(old, new, full=False):
    '''
    Calculate (as possible) difference between two revisions.

    :return:
        List of dicts with keys:
            * ``field_name'';
            * ``field_verbose_name'';
            * ``old'';
            * ``new''.
    '''
    # If content type doesn't match, we can't tell the difference
    if old.content_type_id != new.content_type_id:
        return None
    is_new_full, new = deserialize(new.serialized_data)
    is_old_full, old = deserialize(old.serialized_data)

    if is_new_full and is_old_full:
        return model_diff(old.object, new.object, full=full)


def previous_version(version):
    try:
        return (Version.objects
                    .filter(
                        content_type__id=version.content_type_id,
                        object_id_int=version.object_id_int,
                        pk__lt=version.pk)
                    .order_by('-pk')[0])
    except IndexError:
        return None


class DeserializedRevision(object):

    def __init__(self, revision):
        super(DeserializedRevision, self).__init__()

        self.revision = revision

        versions = (revision.version_set
                            .select_related('content_type')
                            .order_by('content_type'))

        grouped = itr.groupby(
            versions,
            lambda v: '.'.join(
                [v.content_type.app_label, v.content_type.model]))

        self._index = dict(
            (grouper, dict(
                (o.object_id_int, o)# SimpleLazyObject(lambda: o.object_version))
                for o in group))
            for grouper, group in grouped)

    def get_version_for_record(self, record):
        dotted_model_name = '.'.join(
            [record.content_type.app_label,
            record.content_type.model])
        return self._index.get(dotted_model_name, {}).get(record.object_id)

    def get_object_for_record(self, record):
        return deserialize_version(self.get_version_for_record(record))


def deserialize_version(version):
    return deserialize(version.serialized_data, version.format)

deserialize_revision = DeserializedRevision
