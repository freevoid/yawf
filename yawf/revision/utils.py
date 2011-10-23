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


def versions_diff(old, new):
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
        return model_diff(old.object, new.object)
