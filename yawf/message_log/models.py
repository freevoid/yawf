import logging

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

import reversion

from yawf import serialize_utils as json
from yawf.utils import memoizible_property

logger = logging.getLogger(__name__)


class MessageLog(models.Model):

    class Meta:

        get_latest_by = 'created_at'
        ordering = ('created_at',)

    revision = models.ForeignKey('reversion.Revision',
            blank=True, null=True, related_name='message_log')

    uuid = models.CharField(max_length=36,
        db_index=True, unique=True)

    # Date of log
    created_at = models.DateTimeField(auto_now_add=True,
            db_index=True)

    # Generic foreign key to logged instance
    content_type = models.ForeignKey(ContentType,
            related_name='message_logs_instance')
    object_id = models.PositiveIntegerField(db_index=True)
    instance = generic.GenericForeignKey()

    initiator_content_type = models.ForeignKey(ContentType,
            related_name='message_logs_initiator',
            null=True, blank=True)
    initiator_object_id = models.PositiveIntegerField(db_index=True, null=True, blank=True)
    initiator = generic.GenericForeignKey('initiator_content_type', 'initiator_object_id')

    message = models.CharField(max_length=32)
    message_params = models.TextField()

    workflow_id = models.CharField(max_length=64, db_index=True, default='')
    parent_uuid = models.CharField(max_length=36,
        db_index=True, null=True, blank=True)
    group_uuid = models.CharField(max_length=36,
        db_index=True, null=True, blank=True)

    @memoizible_property
    def deserialized_params(self):
        return json.loads(self.message_params)

    @staticmethod
    def serialize_params(params):
        return json.dumps(params)


def log_record_params(sender, **kwargs):
    message = kwargs['message']
    instance = kwargs['new_instance']
    transition_result = kwargs['transition_result']

    initiator = message.sender\
                if isinstance(message.sender, models.Model) else None

    create_dict = dict(
        uuid=message.unique_id,
        message=message.id,
        message_params=MessageLog.serialize_params(message.params),
        workflow_id=sender,
        instance=instance,
        parent_uuid=message.parent_message_id,
        group_uuid=message.message_group,
    )

    if initiator:
        create_dict['initiator'] = initiator

    return create_dict


def main_record_for_revision(revision):
    return revision.message_log.get(parent_uuid__isnull=True)


def ensure_logging(obj, message_kwargs):
    message_lookup = {
        'uuid': message_kwargs['uuid'],
        'message': message_kwargs['message'],
        'workflow_id': message_kwargs['workflow_id'],
    }

    if not MessageLog.objects.filter(**message_lookup).exists():
        try:
            revision_id = (reversion.get_for_object(obj)
                                .values_list('revision_id', flat=True)[0])
        except IndexError:
            revision_id = None
        message_kwargs['revision_id'] = revision_id
        MessageLog.objects.create(**message_kwargs)
