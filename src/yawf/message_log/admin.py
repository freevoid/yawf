from django.contrib import admin
from yawf.message_log.models import MessageLog


class MessageLogAdmin(admin.ModelAdmin):

    list_display = (
        'created_at', 'instance', 'revision_before',
        'revision_after', 'initiator', 'message')

admin.site.register(MessageLog, MessageLogAdmin)
