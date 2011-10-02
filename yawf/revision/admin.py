from django.contrib import admin

from yawf.revision.models import Revision


class RevisionAdmin(admin.ModelAdmin):

    list_display = ('created_at', 'instance', 'revision')

admin.site.register(Revision, RevisionAdmin)
