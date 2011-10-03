import warnings

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from yawf.config import (REVISION_ATTR, REVISION_CONTROLLED_MODELS,
    MESSAGE_LOG_ENABLED, REVISION_ENABLED)
from yawf.base_model import WorkflowAwareModelBase
from yawf.serialize_utils import serialize, deserialize
from yawf.utils import model_diff_fields, model_diff
from yawf.revision import RevisionModelMixin


class Revision(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
    instance = generic.GenericForeignKey()

    revision = models.PositiveIntegerField(db_index=True)
    is_created = models.BooleanField(db_index=True, default=False)

    serialized_fields = models.TextField()

    if MESSAGE_LOG_ENABLED:
        message_log_record = models.ForeignKey('message_log.MessageLog',
            null=True, blank=True, related_name='affected_revisions')

    def deserialize(self):
        return deserialize(self.serialized_fields)

    @classmethod
    def save_revision(cls, obj, message_log_record=None, is_created=False):

        if isinstance(obj, WorkflowAwareModelBase):
            clarified = obj.get_clarified_instance()
        else:
            clarified = obj

        if MESSAGE_LOG_ENABLED:
            cls.objects.create(
                revision=getattr(obj, REVISION_ATTR),
                instance=obj,
                is_created=is_created,
                serialized_fields=serialize(clarified),
                message_log_record=message_log_record,
            )
        else:
            cls.objects.create(
                revision=getattr(obj, REVISION_ATTR),
                instance=obj,
                is_created=is_created,
                serialized_fields=serialize(clarified),
            )

    def diff_fields(self, other):
        # If content type doesn't match, we can't tell the difference
        if self.content_type_id != other.content_type_id:
            return None
        is_new_full, new = self.deserialize()
        is_old_full, old = other.deserialize()

        if is_new_full and is_old_full:
            return model_diff_fields(old.object, new.object)

    def diff(self, other):
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
        if self.content_type_id != other.content_type_id:
            return None
        is_new_full, new = self.deserialize()
        is_old_full, old = other.deserialize()

        if is_new_full and is_old_full:
            return model_diff(old.object, new.object)

    def __unicode__(self):
        return u'%s:%d:%d' % (self.content_type, self.object_id, self.revision)

    class Meta:
        unique_together = [('object_id', 'content_type', 'revision')]


def log_revision(sender, **kwargs):
    instance = kwargs['instance']
    is_created = kwargs['created']
    Revision.save_revision(instance, is_created=is_created)


def setup_handlers(dotted_list=REVISION_CONTROLLED_MODELS):
    # setup revision handler for revised models
    for dotted_cls in dotted_list:
        app_label, model_name = dotted_cls.split('.')
        model_cls = models.get_model(app_label, model_name)

        if not issubclass(model_cls, RevisionModelMixin):
            warnings.warn(
                "You should base model %s on RevisionModelMixin in order to control"
                " its revisions" % dotted_cls)
        models.signals.post_save.connect(log_revision, sender=model_cls)


if REVISION_ENABLED:
    setup_handlers()
