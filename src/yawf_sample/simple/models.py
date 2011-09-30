from django.db import models


class WINDOW_OPEN_STATUS:

    MINIMIZED = 'minimized'
    MAXIMIZED = 'maximized'
    NORMAL = 'normal'

    types = (MINIMIZED, MAXIMIZED, NORMAL)
    choices = zip(types, types)


class Window(models.Model):

    title = models.CharField(max_length=255)
    width = models.IntegerField()
    height = models.IntegerField()

    open_status = models.CharField(
        max_length=32,
        choices=WINDOW_OPEN_STATUS.choices,
        default='init',
        editable=False)
