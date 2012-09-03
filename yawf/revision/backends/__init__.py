class RevisionManager(object):

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def bind_revision(self, obj, attrname='revision'):
        pass
