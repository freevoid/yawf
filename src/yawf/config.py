from django.conf import settings

DEFAULT_CONFIG = {
    'WORKFLOW_TYPE_ATTR': 'workflow_type',
    'REVISION_ATTR': 'revision',
    'INITIAL_STATE': 'init',
    'STATE_TYPE_CONSTRAINT': basestring,
    'DEFAULT_START_MESSAGE': 'start_workflow',
}

CONFIG = DEFAULT_CONFIG.copy()

custom_config = getattr(settings, 'YAWF_CONFIG', None)

if custom_config:
    CONFIG.update(custom_config)

locals().update(CONFIG)
