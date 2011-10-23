from django.contrib import admin
from yawf.message_log.models import MessageLog


class MessageLogAdmin(admin.ModelAdmin):

    ordering = ('-created_at',)
    list_display = (
        'created_at', 'instance', 'revision', 'initiator', 'message', 'uuid', 'group_uuid')

admin.site.register(MessageLog, MessageLogAdmin)
