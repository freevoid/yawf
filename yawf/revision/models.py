from django.db import models
from django.contrib.contenttypes import generic


class RevisionModelMixin(models.Model):

    class Meta:
        abstract = True

    _has_revision_support = True

    revision = models.PositiveIntegerField(default=0,
        db_index=True, editable=False)

    versions = generic.GenericRelation('reversion.Version')

    def save(self, *args, **kwargs):
        self.revision += 1
        super(RevisionModelMixin, self).save(*args, **kwargs)
