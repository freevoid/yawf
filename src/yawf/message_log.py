from collections import Iterable

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from yawf import serialize_utils as json

from yawf.revision import Revision
from yawf.config import MESSAGE_LOG_ENABLED
from yawf.signals import message_handled


class MessageLog(models.Model):

    class Meta:

        get_latest_by = 'created_at'
        ordering = ('created_at',)

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

    revision_before = models.ForeignKey(Revision, related_name='post_message', null=True)
    revision_after = models.ForeignKey(Revision, related_name='pre_message', null=True)


def log_message(sender, **kwargs):
    message = kwargs['message']
    instance = kwargs['instance']
    transition_result = kwargs['transition_result']
    current_revision = instance.revision
    new_revision = kwargs.get('new_revision', (current_revision+1))

    initiator = message.sender\
                if isinstance(message.sender, models.Model) else None

    instance_ct = ContentType.objects.get_for_model(instance)

    if current_revision:
        revision = Revision.objects.only('id').get(
            object_id=instance.id,
            content_type=instance_ct,
            revision=current_revision)
    else:
        revision = None

    new_revision = Revision.objects.only('id').get(
        object_id=instance.id,
        content_type=instance_ct,
        revision=new_revision)

    log_record = MessageLog.objects.create(
        initiator=initiator,
        message=message.id,
        message_params=json.dumps(message.params),
        revision_before=revision,
        revision_after=new_revision,
        instance=instance,
    )

    if isinstance(transition_result, Iterable):
        for affected_obj in transition_result:
            if hasattr(affected_obj, '_has_revision_support'):
                Revision.objects.only('id').filter(
                    object_id=affected_obj.id,
                    content_type=ContentType.objects.get_for_model(affected_obj),
                    revision=affected_obj.revision).update(message_log_record=log_record)
            else:
                # TODO: log/warn
                pass


if MESSAGE_LOG_ENABLED:
    message_handled.connect(log_message)
