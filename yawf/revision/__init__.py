from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

from yawf.config import REVISION_BACKEND


def get_class_from_dotted_path(import_path):

    """
    Imports the message storage class described by import_path, where
    import_path is the full Python path to the class.
    """
    try:
        dot = import_path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured("%s isn't a Python path." % import_path)
    module, classname = import_path[:dot], import_path[dot + 1:]
    try:
        mod = import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured('Error importing module %s: "%s"' %
                                   (module, e))
    try:
        return getattr(mod, classname)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" '
                                   'class.' % (module, classname))


default_revision_manager = get_class_from_dotted_path(REVISION_BACKEND)
from .models import RevisionModelMixin
