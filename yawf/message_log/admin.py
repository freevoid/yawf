from django.contrib import admin
from yawf.message_log.models import MessageLog


class MessageLogAdmin(admin.ModelAdmin):

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_filter = ('workflow_id', 'message')
    list_display = (
        'id', 'created_at', 'workflow_id', 'object_id', 'message', 'initiator',
        'uuid', 'group_uuid')

admin.site.register(MessageLog, MessageLogAdmin,)
