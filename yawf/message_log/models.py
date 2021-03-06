import logging
from collections import Iterable

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


from yawf import serialize_utils as json
from yawf.handlers import SerializibleHandlerResult

logger = logging.getLogger(__name__)


class MessageLog(models.Model):

    class Meta:

        get_latest_by = 'created_at'
        ordering = ('created_at',)

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
    initiator_object_id = models.PositiveIntegerField(
            db_index=True, null=True, blank=True)
    initiator = generic.GenericForeignKey(
            'initiator_content_type', 'initiator_object_id')

    message = models.CharField(max_length=32)
    message_params = models.TextField()
    message_params_dehydrated = models.TextField(default='')

    transition_result = models.TextField(default='')

    workflow_id = models.CharField(max_length=64, db_index=True, default='')
    parent_uuid = models.CharField(max_length=36,
            db_index=True, null=True, blank=True)
    group_uuid = models.CharField(max_length=36,
            db_index=True, null=True, blank=True)

    revision_content_type = models.ForeignKey(ContentType,
            null=True, blank=True, related_name='message_logs_revision')
    revision_id = models.PositiveIntegerField(
            db_index=True, null=True, blank=True)
    revision = generic.GenericForeignKey('revision_content_type', 'revision_id')

    deserialized_params = json.json_converter(
        'message_params')
    deserialized_params_dehydrated = json.json_converter(
        'message_params_dehydrated')
    deserialized_transition_result = json.json_converter(
        'transition_result')

    @staticmethod
    def serialize_params(params):
        return json.dumps(params)


def log_message(sender, **kwargs):
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

    log_record = MessageLog(**create_dict)
    log_record.deserialized_params = message.params
    log_record.deserialized_params_dehydrated = message.dehydrated_params

    if isinstance(transition_result, Iterable):
        log_record.deserialized_transition_result = filter(
            lambda x: isinstance(x, SerializibleHandlerResult),
            transition_result)
    elif isinstance(transition_result, SerializibleHandlerResult):
        log_record.deserialized_transition_result = [transition_result]

    log_record.save()

    return log_record


def main_record_for_revision(revision):
    ct = ContentType.objects.get_for_model(type(revision))
    return MessageLog.objects.get(
        revision_content_type=ct,
        revision_id=revision.pk,
        parent_uuid__isnull=True)
