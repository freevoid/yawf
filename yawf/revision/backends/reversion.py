from __future__ import absolute_import
import reversion

from . import RevisionManager

# revision_merger is a little hack for reversion to "merge" optional
# revision information to records
class ReversionMerger(object):

    def __init__(self, attrname):
        self.attrname = attrname
        super(ReversionMerger, self).__init__()

    def create(self, revision, obj):
        setattr(obj, self.attrname, revision)
        obj.save()

    def db_manager(self, db):
        return self

    @property
    def _default_manager(self):
        return self


class ReversionRevisionManager(RevisionManager):

    def __enter__(self):
        self._reversion_manager = reversion.create_revision()
        self._reversion_manager.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._reversion_manager.__exit__(exc_type, exc_value, traceback)

    def bind_revision(self, obj, attrname='revision'):
        reversion.add_meta(ReversionMerger(attrname), obj=obj)
