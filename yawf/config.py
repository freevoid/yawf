from django.conf import settings

DEFAULT_CONFIG = {
    'WORKFLOW_TYPE_ATTR': 'workflow_type',
    'INITIAL_STATE': 'init',
    'STATE_TYPE_CONSTRAINT': basestring,
    'DEFAULT_START_MESSAGE': 'start_workflow',
    'SOFT_DELETE_ATTR': None,
    'REVISION_ATTR': 'revision',
    'MESSAGE_LOG_ENABLED': False,
    'TRANSACTIONAL_SIDE_EFFECT': True,
    'USE_SELECT_FOR_UPDATE': True,
    'REVISION_BACKEND':
        'yawf.revision.backends.reversion.ReversionRevisionManager',
}

CONFIG = DEFAULT_CONFIG.copy()

custom_config = getattr(settings, 'YAWF_CONFIG', None)

if custom_config:
    CONFIG.update(custom_config)

locals().update(CONFIG)
