from django.contrib import admin
from yawf.config import REVISION_ENABLED, MESSAGE_LOG_ENABLED

if REVISION_ENABLED:

    from yawf.revision import Revision

    class RevisionAdmin(admin.ModelAdmin):

        list_display = ('created_at', 'instance', 'revision')

    admin.site.register(Revision, RevisionAdmin)

    if MESSAGE_LOG_ENABLED:

        from yawf.message_log import MessageLog

        class MessageLogAdmin(admin.ModelAdmin):

            list_display = (
                'created_at', 'instance', 'revision_before',
                'revision_after', 'initiator', 'message')

        admin.site.register(MessageLog, MessageLogAdmin)
