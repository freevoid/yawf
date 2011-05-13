from django.conf import settings

DEFAULT_CONFIG = {
    'WORKFLOW_TYPE_ATTR': 'workflow_type',
    'INITIAL_STATE': 'init',
    'STATE_TYPE_CONSTRAINT': basestring,
    'DEFAULT_START_MESSAGE': 'start_workflow',
}

CONFIG = getattr(settings, 'YAWF_CONFIG', DEFAULT_CONFIG)

locals().update(CONFIG)
