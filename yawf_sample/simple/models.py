from django.db import models

import reversion
from yawf.revision import RevisionModelMixin


class WINDOW_OPEN_STATUS:

    MINIMIZED = 'minimized'
    MAXIMIZED = 'maximized'
    NORMAL = 'normal'

    types = (MINIMIZED, MAXIMIZED, NORMAL)
    choices = zip(types, types)


class Window(RevisionModelMixin, models.Model):

    title = models.CharField(max_length=255)
    width = models.IntegerField()
    height = models.IntegerField()

    workflow_type = 'simple'

    open_status = models.CharField(
        max_length=32,
        choices=WINDOW_OPEN_STATUS.choices,
        default='init',
        editable=False)

reversion.register(Window)
