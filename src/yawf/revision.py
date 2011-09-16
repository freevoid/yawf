import warnings

from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.core import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils import simplejson as json

from yawf.config import REVISION_ATTR, REVISION_CONTROLLED_MODELS, MESSAGE_LOG_ENABLED
from yawf.base_model import WorkflowAwareModelBase


def serialize(instance):
    serializer = serializers.get_serializer("json")()
    serializer.serialize([instance], ensure_ascii=False)
    return serializer.getvalue()


def deserialize_to_dict(content):
    item = json.loads(content)[0]
    return item['fields']


def deserialize(content):
    try:
        deserialized = serializers.deserialize("json", content).next()
    except FieldDoesNotExist:
        deserialize_to_dict(content)
    else:
        return deserialized


class Revision(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
    instance = generic.GenericForeignKey()

    revision = models.PositiveIntegerField(db_index=True)

    serialized_fields = models.TextField()

    if MESSAGE_LOG_ENABLED:
        message_log_record = models.ForeignKey('yawf.MessageLog',
            null=True, blank=True, related_name='affected_revisions')

    @property
    def deserialized(self):
        return deserialize(self.serialized_fields)

    @classmethod
    def save_revision(cls, obj, message_log_record=None):

        if isinstance(obj, WorkflowAwareModelBase):
            clarified = obj.get_clarified_instance()
        else:
            clarified = obj

        cls.objects.create(
            revision=getattr(obj, REVISION_ATTR),
            instance=obj,
            serialized_fields=serialize(clarified),
            message_log_record=message_log_record,
        )

    def __unicode__(self):
        return u'%s:%d:%d' % (self.content_type, self.object_id, self.revision)

    class Meta:
        unique_together = [('object_id', 'content_type', 'revision')]


class RevisionModelMixin(models.Model):

    class Meta:
        abstract = True

    _has_revision_support = True

    revision = models.PositiveIntegerField(default=0,
        db_index=True, editable=False)

    def save(self, *args, **kwargs):
        self.revision += 1
        super(RevisionModelMixin, self).save(*args, **kwargs)


def log_revision(sender, **kwargs):
    instance = kwargs['instance']
    Revision.save_revision(instance)


def setup_handlers(dotted_list=REVISION_CONTROLLED_MODELS):
    # setup revision handler for revised models
    for dotted_cls in dotted_list:
        app_label, model_name = dotted_cls.split('.')
        model_cls = models.get_model(app_label, model_name)

        if not issubclass(model_cls, RevisionModelMixin):
            warnings.warning(
                "You should base model %s on RevisionModelMixin in order to control"
                " its revisions" % dotted_cls)
        models.signals.post_save.connect(log_revision, sender=model_cls)
