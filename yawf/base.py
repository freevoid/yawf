import warnings

warnings.warn(
    'Use of yawf.base is DEPRECATED. Use yawf.workflow instead.',
    DeprecationWarning)
from .workflow import WorkflowBase
