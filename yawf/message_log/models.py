from collections import Iterable

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from yawf import serialize_utils as json

from yawf.revision.models import Revision
from yawf.config import MESSAGE_LOG_ENABLED
from yawf.signals import message_handled
from yawf.utils import memoizible_property


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

    workflow_id = models.CharField(max_length=64, db_index=True, default='')
    parent_id = models.ForeignKey('self', blank=True, null=True)

    @memoizible_property
    def deserialized_params(self):
        return json.loads(self.message_params)

    @staticmethod
    def serialize_params(params):
        return json.dumps(params)


def log_message(sender, **kwargs):
    message = kwargs['message']
    instance = kwargs['instance']
    new_instance = kwargs['new_instance']
    transition_result = kwargs['transition_result']
    if hasattr(instance, 'revision'):
        current_revision = instance.revision
        new_revision_id = new_instance.revision
    else:
        current_revision = new_revision_id = None

    initiator = message.sender\
                if isinstance(message.sender, models.Model) else None

    instance_ct = ContentType.objects.get_for_model(instance)

    if current_revision:
        try:
            revision = Revision.objects.only('id').get(
                object_id=instance.id,
                content_type=instance_ct,
                revision=current_revision)
        except Revision.DoesNotExist:
            revision = None
    else:
        revision = None

    if new_revision_id:
        try:
            new_revision = Revision.objects.only('id').get(
                object_id=instance.id,
                content_type=instance_ct,
                revision=new_revision_id)
        except Revision.DoesNotExist:
            new_revision = None
    else:
        new_revision = None

    create_dict = dict(
        message=message.id,
        message_params=MessageLog.serialize_params(message.params),
        workflow_id=sender,
        revision_before=revision,
        revision_after=new_revision,
        instance=instance,
    )
    if initiator:
        create_dict['initiator'] = initiator
    log_record = MessageLog.objects.create(**create_dict)

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
